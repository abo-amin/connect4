from flask import render_template, redirect, url_for, request, jsonify, flash, session
from flask_login import login_required, current_user
from datetime import datetime
import json

from social import social_bp
from models import db, User, Friendship, Message, Notification, FriendshipStatus, MessageStatus, NotificationType

@social_bp.route('/friends')
@login_required
def friends():
    """Display friend list and friend requests"""
    # Get friend list
    friends = current_user.get_friends()
    
    # Get pending friend requests
    friend_requests = current_user.get_friend_requests()
    
    return render_template('social/friends.html', 
                           friends=friends, 
                           friend_requests=friend_requests)

@social_bp.route('/add_friend', methods=['POST'])
@login_required
def add_friend():
    """Send friend request to another user"""
    username = request.form.get('username')
    
    if not username:
        flash('Please enter a username', 'danger')
        return redirect(url_for('social.friends'))
    
    # Don't allow adding yourself
    if username == current_user.username:
        flash('You cannot add yourself as a friend', 'danger')
        return redirect(url_for('social.friends'))
    
    # Check if user exists
    user = User.query.filter_by(username=username).first()
    if not user:
        flash(f'User {username} not found', 'danger')
        return redirect(url_for('social.friends'))
    
    # Check if already friends or request pending
    existing = Friendship.query.filter(
        ((Friendship.sender_id == current_user.id) & (Friendship.receiver_id == user.id)) |
        ((Friendship.sender_id == user.id) & (Friendship.receiver_id == current_user.id))
    ).first()
    
    if existing:
        if existing.status == FriendshipStatus.ACCEPTED.value:
            flash(f'You are already friends with {username}', 'warning')
        elif existing.status == FriendshipStatus.PENDING.value:
            if existing.sender_id == current_user.id:
                flash(f'Friend request to {username} is already pending', 'info')
            else:
                flash(f'{username} has already sent you a friend request', 'info')
        elif existing.status == FriendshipStatus.REJECTED.value:
            # If previously rejected, update to pending
            existing.status = FriendshipStatus.PENDING.value
            existing.updated_at = datetime.utcnow()
            db.session.commit()
            flash(f'Friend request sent to {username}', 'success')
            
            # Create notification for the receiver
            notification = Notification(
                user_id=user.id,
                type=NotificationType.FRIEND_REQUEST.value,
                message=f'{current_user.username} sent you a friend request',
                data=json.dumps({'sender_id': current_user.id, 'sender_name': current_user.username})
            )
            db.session.add(notification)
            db.session.commit()
        return redirect(url_for('social.friends'))
    
    # Create new friendship request
    friendship = Friendship(
        sender_id=current_user.id,
        receiver_id=user.id,
        status=FriendshipStatus.PENDING.value
    )
    db.session.add(friendship)
    
    # Create notification for the receiver
    notification = Notification(
        user_id=user.id,
        type=NotificationType.FRIEND_REQUEST.value,
        message=f'{current_user.username} sent you a friend request',
        data=json.dumps({'sender_id': current_user.id, 'sender_name': current_user.username})
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f'Friend request sent to {username}', 'success')
    return redirect(url_for('social.friends'))

@social_bp.route('/accept_friend/<int:request_id>', methods=['POST'])
@login_required
def accept_friend(request_id):
    """Accept a friend request"""
    friendship = Friendship.query.filter_by(id=request_id, receiver_id=current_user.id).first_or_404()
    
    friendship.status = FriendshipStatus.ACCEPTED.value
    friendship.updated_at = datetime.utcnow()
    
    # Create notification for the sender
    notification = Notification(
        user_id=friendship.sender_id,
        type=NotificationType.FRIEND_REQUEST.value,
        message=f'{current_user.username} accepted your friend request',
        data=json.dumps({'friend_id': current_user.id, 'friend_name': current_user.username})
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f'You are now friends with {friendship.sender.username}', 'success')
    return redirect(url_for('social.friends'))

@social_bp.route('/reject_friend/<int:request_id>', methods=['POST'])
@login_required
def reject_friend(request_id):
    """Reject a friend request"""
    friendship = Friendship.query.filter_by(id=request_id, receiver_id=current_user.id).first_or_404()
    
    friendship.status = FriendshipStatus.REJECTED.value
    friendship.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Friend request from {friendship.sender.username} rejected', 'info')
    return redirect(url_for('social.friends'))

@social_bp.route('/remove_friend/<int:friend_id>', methods=['POST'])
@login_required
def remove_friend(friend_id):
    """Remove a friend from your friend list"""
    friendship = Friendship.query.filter(
        ((Friendship.sender_id == current_user.id) & (Friendship.receiver_id == friend_id)) |
        ((Friendship.sender_id == friend_id) & (Friendship.receiver_id == current_user.id)),
        Friendship.status == FriendshipStatus.ACCEPTED.value
    ).first_or_404()
    
    # Get the friend's username for the flash message
    friend = User.query.get_or_404(friend_id)
    
    db.session.delete(friendship)
    db.session.commit()
    
    flash(f'{friend.username} has been removed from your friends', 'info')
    return redirect(url_for('social.friends'))

@social_bp.route('/leaderboard')
@login_required
def leaderboard():
    """Display leaderboard of top players"""
    # Get top 10 players by win rate (minimum 5 games)
    top_win_rate = User.query.filter(User.total_games >= 5).order_by(User.wins / User.total_games * 100).limit(10).all()
    
    # Get top 10 players by most wins
    top_wins = User.query.order_by(User.wins.desc()).limit(10).all()
    
    # Get top 10 players by most games
    top_games = User.query.order_by(User.total_games.desc()).limit(10).all()
    
    return render_template('social/leaderboard.html', 
                           top_win_rate=top_win_rate,
                           top_wins=top_wins, 
                           top_games=top_games)

@social_bp.route('/messages')
@login_required
def messages():
    """Display message inbox"""
    # Get received messages
    received_msgs = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.created_at.desc()).all()
    
    # Get sent messages
    sent_msgs = Message.query.filter_by(sender_id=current_user.id).order_by(Message.created_at.desc()).all()
    
    return render_template('social/messages.html', 
                           received=received_msgs, 
                           sent=sent_msgs)

@social_bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    """Send a message to another user"""
    username = request.form.get('username')
    content = request.form.get('content')
    
    if not username or not content:
        flash('Please enter both username and message content', 'danger')
        return redirect(url_for('social.messages'))
    
    # Check if user exists
    user = User.query.filter_by(username=username).first()
    if not user:
        flash(f'User {username} not found', 'danger')
        return redirect(url_for('social.messages'))
    
    # Create new message
    message = Message(
        sender_id=current_user.id,
        receiver_id=user.id,
        content=content,
        status=MessageStatus.UNREAD.value
    )
    db.session.add(message)
    
    # Create notification for the receiver
    notification = Notification(
        user_id=user.id,
        type=NotificationType.MESSAGE.value,
        message=f'New message from {current_user.username}',
        data=json.dumps({'sender_id': current_user.id, 'sender_name': current_user.username})
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f'Message sent to {username}', 'success')
    return redirect(url_for('social.messages'))

@social_bp.route('/read_message/<int:message_id>', methods=['POST'])
@login_required
def read_message(message_id):
    """Mark a message as read"""
    message = Message.query.filter_by(id=message_id, receiver_id=current_user.id).first_or_404()
    
    message.mark_as_read()
    db.session.commit()
    
    return jsonify({'success': True})

@social_bp.route('/notifications')
@login_required
def notifications():
    """Display notifications"""
    # Get all notifications for the current user
    user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    return render_template('social/notifications.html', notifications=user_notifications)

@social_bp.route('/mark_notification_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    
    notification.mark_as_read()
    db.session.commit()
    
    return jsonify({'success': True})

@social_bp.route('/mark_all_notifications_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    
    for notification in notifications:
        notification.mark_as_read()
    
    db.session.commit()
    
    return jsonify({'success': True})

@social_bp.route('/invite_friend/<int:friend_id>', methods=['POST'])
@login_required
def invite_friend(friend_id):
    """Invite a friend to play a game"""
    # Check if user is a friend
    if not current_user.is_friend_with(friend_id):
        flash('You can only invite friends to play', 'danger')
        return redirect(url_for('social.friends'))
    
    friend = User.query.get_or_404(friend_id)
    
    # Create notification for the friend
    notification = Notification(
        user_id=friend_id,
        type=NotificationType.GAME_INVITE.value,
        message=f'{current_user.username} invited you to play Connect4',
        data=json.dumps({
            'sender_id': current_user.id, 
            'sender_name': current_user.username,
            'game_url': url_for('dashboard.menu', _external=True)
        })
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f'Game invitation sent to {friend.username}', 'success')
    return redirect(url_for('social.friends'))
