from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import User, ChatMessage, TextAnalysisSession, ImageReflectionTest
import json
import random
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Custom User Creation Form
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

# Home and Auth Views
def home(request):
    """Home page - uses base.html"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'base.html')

@login_required
def dashboard(request):
    """Dashboard view with REAL data"""
    try:
        # Get real data from database
        user_chats = ChatMessage.objects.filter(user=request.user)
        
        # Calculate real metrics
        total_chats = user_chats.count()
        
        # Get last week's data for trends
        week_ago = datetime.now() - timedelta(days=7)
        recent_chats = user_chats.filter(timestamp__gte=week_ago)
        
        # Calculate real sentiment from chat history
        sentiment_data = calculate_real_sentiment(recent_chats)
        risk_data = calculate_real_risk_level(recent_chats)
        
        # Get recent chat preview
        recent_messages = list(recent_chats.order_by('-timestamp')[:5])
        
        context = {
            'total_chats': total_chats,
            'recent_chats_count': recent_chats.count(),
            'sentiment_data': sentiment_data,
            'risk_data': risk_data,
            'recent_messages': recent_messages,
            'user': request.user
        }
        return render(request, 'dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        # Fallback to basic dashboard
        return render(request, 'dashboard.html', {
            'total_chats': 0,
            'recent_chats_count': 0,
            'sentiment_data': {'positive': 0, 'neutral': 100, 'negative': 0},
            'risk_data': {'level': 0, 'category': 'low'},
            'recent_messages': []
        })

def calculate_real_sentiment(chats):
    """Calculate real sentiment from chat messages"""
    if not chats:
        return {'positive': 0, 'neutral': 100, 'negative': 0}
    
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for chat in chats:
        # Use ML sentiment analysis on existing messages
        sentiment = analyze_sentiment_simple(chat.user_message)
        
        if sentiment > 0.1:
            positive_count += 1
        elif sentiment < -0.1:
            negative_count += 1
        else:
            neutral_count += 1
    
    total = len(chats)
    return {
        'positive': round((positive_count / total) * 100, 1),
        'neutral': round((neutral_count / total) * 100, 1),
        'negative': round((negative_count / total) * 100, 1)
    }

def calculate_real_risk_level(chats):
    """Calculate real risk level from chat messages"""
    if not chats:
        return {'level': 0, 'category': 'low'}
    
    total_risk = 0
    for chat in chats:
        risk_data = assess_risk_simple(chat.user_message)
        total_risk += risk_data['risk_level']
    
    avg_risk = total_risk / len(chats)
    
    if avg_risk >= 7:
        category = 'high'
    elif avg_risk >= 4:
        category = 'medium'
    else:
        category = 'low'
    
    return {'level': round(avg_risk, 1), 'category': category}

def user_login(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'auth/login.html', {'error': 'Invalid credentials'})
    return render(request, 'auth/login.html')

def user_logout(request):
    """User logout view"""
    logout(request)
    return redirect('dashboard')

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/register.html', {'form': form})

# Chat Views
@login_required
def chat_view(request):
    """Main chat interface - uses chat/chat.html"""
    return render(request, 'chat/chat.html')

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def chat_message(request):
    """Handle chat messages and save with ML analysis"""
    try:
        message = request.POST.get('message', '').strip()
        
        if not message:
            return JsonResponse({'success': False, 'error': 'Empty message'})
        
        # Generate chatbot response
        bot_response = generate_chatbot_response(message)
        
        # Analyze message with ML
        sentiment_score = analyze_sentiment_simple(message)
        risk_data = assess_risk_simple(message)
        emotions = analyze_emotions_simple(message)
        
        # Save to database with ML analysis
        chat = ChatMessage.objects.create(
            user=request.user,
            user_message=message,
            bot_response=bot_response,
            sentiment_score=sentiment_score,
            risk_level=risk_data['risk_level'],
            emotions=emotions
        )
        
        return JsonResponse({
            'success': True, 
            'response': bot_response,
            'user_message': message,
            'sentiment_score': sentiment_score,
            'risk_level': risk_data['risk_level'],
            'emotions': emotions
        })
        
    except Exception as e:
        logger.error(f"Chat message error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Internal server error'})

def generate_chatbot_response(message):
    """Enhanced chatbot response generator"""
    message_lower = message.lower()
    
    # Mental health focused responses
    if any(word in message_lower for word in ['hello', 'hi', 'hey']):
        return "Hello! I'm MindSight AI. How are you feeling today?"
    elif any(word in message_lower for word in ['sad', 'depressed', 'unhappy', 'down']):
        return "I'm sorry you're feeling this way. It takes courage to acknowledge these feelings. Would you like to talk about what's been on your mind?"
    elif any(word in message_lower for word in ['anxious', 'nervous', 'worried', 'panic']):
        return "Anxiety can feel overwhelming. Let's explore what might be causing these feelings together. Remember to breathe deeply."
    elif any(word in message_lower for word in ['happy', 'good', 'great', 'awesome']):
        return "That's wonderful to hear! Celebrating positive moments is important. What's been going well for you?"
    elif any(word in message_lower for word in ['stress', 'stressed', 'overwhelmed']):
        return "Stress can be challenging. Let's break down what's causing this feeling and explore some coping strategies."
    elif any(word in message_lower for word in ['lonely', 'alone', 'isolated']):
        return "Feeling lonely can be difficult. Remember that reaching out is a sign of strength. Would you like to explore ways to build connections?"
    elif any(word in message_lower for word in ['angry', 'mad', 'frustrated']):
        return "Anger is a natural emotion. Let's explore what's triggering these feelings and find healthy ways to express them."
    elif any(word in message_lower for word in ['thank', 'thanks', 'appreciate']):
        return "You're welcome! I'm here to support you on your mental wellness journey."
    elif any(word in message_lower for word in ['bye', 'goodbye', 'see you']):
        return "Take care of yourself! Remember to practice self-care. I'm here whenever you need to talk."
    elif any(word in message_lower for word in ['help', 'emergency', 'crisis']):
        return "If you're in crisis, please contact emergency services or a crisis helpline immediately. You can also call 988 for mental health support."
    else:
        responses = [
            "I understand. Could you tell me more about how you're feeling?",
            "Thank you for sharing. What's been on your mind lately?",
            "I'm listening. How has your day been going?",
            "That sounds important. Would you like to explore this further?",
            "I appreciate you opening up. Let's continue our conversation."
        ]
        return random.choice(responses)


@login_required
def chat_history(request):
    """Chat history page with REAL data"""
    print(f"📖 CHAT HISTORY - User: {request.user}, Authenticated: {request.user.is_authenticated}")
    try:
        recent_chats = ChatMessage.objects.filter(user=request.user).order_by('-timestamp')[:50]
        
        # Calculate statistics
        total_chats = recent_chats.count()
        if total_chats > 0:
            avg_sentiment = sum(chat.sentiment_score for chat in recent_chats if chat.sentiment_score) / total_chats
            avg_risk = sum(chat.risk_level for chat in recent_chats if chat.risk_level) / total_chats
        else:
            avg_sentiment = 0
            avg_risk = 0
        
        context = {
            'recent_chats': recent_chats,
            'total_chats': total_chats,
            'avg_sentiment': round(avg_sentiment, 2),
            'avg_risk': round(avg_risk, 1),
            'user': request.user  # ✅ FIX: Pass the user object, not just username
        }
        return render(request, 'chat/history.html', context)
        
    except Exception as e:
        logger.error(f"Chat history error: {str(e)}")
        return render(request, 'chat/history.html', {
            'recent_chats': [],
            'total_chats': 0,
            'avg_sentiment': 0,
            'avg_risk': 0,
            'error': 'Unable to load chat history',
            'user': request.user  # ✅ FIX: Always pass user object
        })
@csrf_exempt
@require_http_methods(["POST"])
@login_required
def clear_history(request):
    """Clear all chat history"""
    try:
        deleted_count, _ = ChatMessage.objects.filter(user=request.user).delete()
        
        if deleted_count > 0:
            messages.success(request, f'All {deleted_count} messages cleared successfully.')
        else:
            messages.info(request, 'No messages to clear.')
            
    except Exception as e:
        logger.error(f"Clear history error: {str(e)}")
        messages.error(request, 'Failed to clear chat history. Please try again.')
    
    return redirect('chat_history')

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def delete_single_message(request, message_id):
    """Delete a single chat message - SIMPLE WORKING VERSION"""
    try:
        print(f"Deleting message {message_id} for user {request.user}")
        
        # Simple delete using filter
        deleted_count, _ = ChatMessage.objects.filter(id=message_id, user=request.user).delete()
        
        if deleted_count > 0:
            messages.success(request, 'Message deleted successfully.')
            print(f"✅ Deleted {deleted_count} message(s)")
        else:
            messages.error(request, 'Message not found.')
            print(f"❌ No message found with ID {message_id}")
            
    except Exception as e:
        print(f"Error: {e}")
        messages.error(request, 'Error deleting message.')
    
    return redirect('chat_history')

@login_required
def weekly_report(request):
    """Weekly report page with REAL data"""
    try:
        # Calculate date range for this week
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Get this week's chats
        week_chats = ChatMessage.objects.filter(
            user=request.user,
            timestamp__date__range=[week_start, week_end]
        )
        
        # Calculate real metrics
        total_chats = week_chats.count()
        
        if total_chats > 0:
            sentiment_scores = [chat.sentiment_score for chat in week_chats if chat.sentiment_score is not None]
            risk_levels = [chat.risk_level for chat in week_chats if chat.risk_level is not None]
            
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            avg_risk = sum(risk_levels) / len(risk_levels) if risk_levels else 0
            
            # Determine dominant emotion based on sentiment
            if avg_sentiment > 0.3:
                dominant_emotion = 'positive'
            elif avg_sentiment < -0.3:
                dominant_emotion = 'concerned'
            else:
                dominant_emotion = 'neutral'
                
            # Risk trend (simple comparison with last week)
            last_week_start = week_start - timedelta(days=7)
            last_week_end = week_start - timedelta(days=1)
            last_week_chats = ChatMessage.objects.filter(
                user=request.user,
                timestamp__date__range=[last_week_start, last_week_end]
            )
            
            if last_week_chats.count() > 0:
                last_week_risk = sum(chat.risk_level for chat in last_week_chats if chat.risk_level) / last_week_chats.count()
                risk_trend = 'decreasing' if avg_risk < last_week_risk else 'increasing' if avg_risk > last_week_risk else 'stable'
            else:
                risk_trend = 'stable'
                
            # **NEW: Calculate daily data for charts**
            week_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            daily_messages = []
            daily_sentiment = []
            
            # Calculate data for each day of the week
            for i in range(7):
                day_date = week_start + timedelta(days=i)
                day_chats = week_chats.filter(timestamp__date=day_date)
                
                # Daily message count
                daily_messages.append(day_chats.count())
                
                # Daily average sentiment
                if day_chats.exists():
                    day_sentiments = [chat.sentiment_score for chat in day_chats if chat.sentiment_score is not None]
                    daily_sentiment.append(round(sum(day_sentiments) / len(day_sentiments), 2) if day_sentiments else 0)
                else:
                    daily_sentiment.append(0)
            
            # **NEW: Calculate risk distribution**
            low_risk_count = week_chats.filter(risk_level__lt=4).count()
            medium_risk_count = week_chats.filter(risk_level__gte=4, risk_level__lt=7).count()
            high_risk_count = week_chats.filter(risk_level__gte=7).count()
            
            total_risk_chats = low_risk_count + medium_risk_count + high_risk_count
            if total_risk_chats > 0:
                risk_distribution = [
                    round((low_risk_count / total_risk_chats) * 100),
                    round((medium_risk_count / total_risk_chats) * 100),
                    round((high_risk_count / total_risk_chats) * 100)
                ]
            else:
                risk_distribution = [0, 0, 0]
                
        else:
            avg_sentiment = 0
            avg_risk = 0
            dominant_emotion = 'neutral'
            risk_trend = 'stable'
            # **NEW: Empty data for no chats**
            week_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            daily_messages = [0, 0, 0, 0, 0, 0, 0]
            daily_sentiment = [0, 0, 0, 0, 0, 0, 0]
            risk_distribution = [0, 0, 0]
        
        # Generate insights based on real data
        insights = generate_weekly_insights(week_chats, avg_sentiment, avg_risk)
        recommendations = generate_weekly_recommendations(avg_sentiment, avg_risk, total_chats)
        
        context = {
            'week_start': week_start.strftime('%Y-%m-%d'),
            'week_end': week_end.strftime('%Y-%m-%d'),
            'total_chats': total_chats,
            'average_sentiment': round(avg_sentiment, 2),
            'dominant_emotion': dominant_emotion,
            'risk_trend': risk_trend,
            'average_risk': round(avg_risk, 1),
            'insights': insights,
            'recommendations': recommendations,
            'has_data': total_chats > 0,
            # **NEW: Chart data**
            'week_days': week_days,
            'daily_messages': daily_messages,
            'daily_sentiment': daily_sentiment,
            'risk_distribution': risk_distribution,
        }
        return render(request, 'reports/weekly.html', context)
        
    except Exception as e:
        logger.error(f"Weekly report error: {str(e)}")
        return render(request, 'reports/weekly.html', {
            'error': 'Unable to generate weekly report',
            'has_data': False,
            'week_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'daily_messages': [0, 0, 0, 0, 0, 0, 0],
            'daily_sentiment': [0, 0, 0, 0, 0, 0, 0],
            'risk_distribution': [0, 0, 0],
        })

def generate_weekly_insights(chats, avg_sentiment, avg_risk):
    """Generate insights based on real chat data"""
    insights = []
    total_chats = chats.count()
    
    if total_chats == 0:
        return ["Start chatting with MindSight to get personalized insights!"]
    
    # Engagement insight
    if total_chats >= 10:
        insights.append("Great engagement this week! You've been consistently checking in.")
    elif total_chats >= 5:
        insights.append("Good start this week. Consider increasing your chat frequency for better insights.")
    else:
        insights.append("Try to engage more with MindSight to get the most out of your mental wellness journey.")
    
    # Sentiment-based insights
    if avg_sentiment > 0.5:
        insights.append("Your positive sentiment patterns show good emotional resilience.")
    elif avg_sentiment < -0.3:
        insights.append("We noticed some challenging emotions this week. Remember, it's okay to not be okay.")
    else:
        insights.append("You've maintained emotional stability throughout the week.")
    
    # Risk-based insights
    if avg_risk >= 7:
        insights.append("Higher risk patterns detected. Please prioritize self-care and consider professional support.")
    elif avg_risk >= 4:
        insights.append("Moderate stress levels observed. The coping strategies we discussed can help.")
    else:
        insights.append("Good emotional regulation and low risk patterns this week.")
    
    return insights

def generate_weekly_recommendations(avg_sentiment, avg_risk, total_chats):
    """Generate personalized recommendations"""
    recommendations = []
    
    # Base recommendations for everyone
    recommendations.append({
        'title': 'Daily Mindfulness',
        'description': 'Practice 5 minutes of mindfulness meditation each day',
        'icon': '🧘',
        'reason': 'Builds emotional awareness'
    })
    
    # Sentiment-based recommendations
    if avg_sentiment < 0:
        recommendations.append({
            'title': 'Gratitude Journal',
            'description': 'Write down three things you appreciate each day',
            'icon': '📝',
            'reason': 'Helps shift focus to positive aspects'
        })
    
    # Risk-based recommendations
    if avg_risk >= 4:
        recommendations.append({
            'title': 'Breathing Exercises',
            'description': 'Try 4-7-8 breathing when feeling overwhelmed',
            'icon': '🌬️',
            'reason': 'Effective for stress reduction'
        })
    
    # Engagement-based recommendations
    if total_chats < 5:
        recommendations.append({
            'title': 'Regular Check-ins',
            'description': 'Chat with MindSight daily to track your mood',
            'icon': '💬',
            'reason': 'Consistent tracking improves insights'
        })
    
    return recommendations

# ML Analysis Views
@csrf_exempt
@require_http_methods(["POST"])
@login_required
def analyze_message(request):
    """Analyze message with ML models"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        
        if not message:
            return JsonResponse({'error': 'No message provided'}, status=400)
        
        # ML analysis
        sentiment_score = analyze_sentiment_simple(message)
        emotions = analyze_emotions_simple(message)
        risk_data = assess_risk_simple(message)
        
        response_data = {
            'analysis': {
                'emotions': emotions,
                'dominant_emotion': max(emotions.items(), key=lambda x: x[1])[0],
                'sentiment_score': sentiment_score
            },
            'risk_assessment': risk_data,
            'recommendations': get_simple_recommendations(risk_data['risk_level']),
            'ml_available': True
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Message analysis error: {str(e)}")
        return JsonResponse({'error': 'Analysis failed'}, status=500)

# ML Helper Functions
def analyze_sentiment_simple(text):
    """Enhanced sentiment analysis using keyword matching"""
    text_lower = text.lower()
    
    positive_words = ['good', 'great', 'happy', 'joy', 'love', 'nice', 'well', 'better', 'amazing', 'wonderful', 'excited', 'proud', 'grateful', 'thankful', 'calm', 'peaceful']
    negative_words = ['bad', 'sad', 'angry', 'hate', 'terrible', 'awful', 'worst', 'depressed', 'anxious', 'stressed', 'overwhelmed', 'lonely', 'scared', 'fear', 'panic', 'hopeless']
    
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    total = positive_count + negative_count
    if total == 0:
        return 0.0
    
    sentiment = (positive_count - negative_count) / total
    return max(-1.0, min(1.0, sentiment))

def analyze_emotions_simple(text):
    """Enhanced emotion analysis using keyword matching"""
    text_lower = text.lower()
    
    emotions = {
        'joy': 0.0,
        'sadness': 0.0, 
        'anger': 0.0,
        'fear': 0.0,
        'calm': 0.0,
        'neutral': 0.3  # Base neutral level
    }
    
    # Joy indicators
    joy_words = ['happy', 'joy', 'excited', 'good', 'great', 'love', 'wonderful', 'amazing', 'proud', 'grateful']
    if any(word in text_lower for word in joy_words):
        emotions['joy'] = 0.8
        emotions['neutral'] = 0.1
    
    # Sadness indicators
    sadness_words = ['sad', 'depressed', 'unhappy', 'cry', 'tears', 'hopeless', 'empty', 'alone']
    if any(word in text_lower for word in sadness_words):
        emotions['sadness'] = 0.7
        emotions['neutral'] = 0.2
    
    # Anger indicators  
    anger_words = ['angry', 'mad', 'hate', 'furious', 'annoyed', 'frustrated', 'rage']
    if any(word in text_lower for word in anger_words):
        emotions['anger'] = 0.6
        emotions['neutral'] = 0.3
    
    # Fear indicators
    fear_words = ['scared', 'afraid', 'fear', 'anxious', 'worried', 'nervous', 'panic', 'terrified']
    if any(word in text_lower for word in fear_words):
        emotions['fear'] = 0.6
        emotions['neutral'] = 0.3
    
    # Calm indicators
    calm_words = ['calm', 'peaceful', 'relaxed', 'serene', 'content', 'okay', 'fine']
    if any(word in text_lower for word in calm_words):
        emotions['calm'] = 0.7
        emotions['neutral'] = 0.2
    
    # Normalize to sum to 1.0
    total = sum(emotions.values())
    return {k: round(v/total, 3) for k, v in emotions.items()}

def faq_quiz(request):
    return render(request, 'chat/faq_quiz.html')

def assess_risk_simple(text):
    """Enhanced risk assessment"""
    text_lower = text.lower()
    
    high_risk_words = ['suicide', 'kill myself', 'want to die', 'end it all', 'harm myself', 'better off dead']
    medium_risk_words = ['depressed', 'hopeless', 'cant cope', 'overwhelmed', 'cant take it', 'giving up']
    low_risk_words = ['sad', 'anxious', 'stressed', 'worried', 'nervous', 'upset']
    
    high_count = sum(1 for word in high_risk_words if word in text_lower)
    medium_count = sum(1 for word in medium_risk_words if word in text_lower) 
    low_count = sum(1 for word in low_risk_words if word in text_lower)
    
    risk_level = high_count * 8 + medium_count * 4 + low_count * 2
    risk_level = min(10, max(0, risk_level))
    
    if risk_level >= 7:
        category = 'high'
    elif risk_level >= 4:
        category = 'medium'
    else:
        category = 'low'
    
    return {'risk_level': risk_level, 'risk_category': category}

def get_simple_recommendations(risk_level):
    """Get recommendations based on risk level"""
    recommendations = [
        {
            'id': 1,
            'title': 'Deep Breathing',
            'description': 'Take 5 deep breaths to calm your mind',
            'type': 'anxiety',
            'duration': 2,
            'icon': '🌬️'
        },
        {
            'id': 2, 
            'title': 'Positive Reflection',
            'description': 'Recall one positive thing from today',
            'type': 'depression',
            'duration': 1,
            'icon': '💭'
        }
    ]
    
    if risk_level >= 7:
        recommendations.append({
            'id': 3,
            'title': 'Emergency Support',
            'description': 'Contact crisis helpline for immediate help',
            'type': 'emergency', 
            'duration': 0,
            'icon': '🚨',
            'emergency': True
        })
    
    if risk_level >= 4:
        recommendations.append({
            'id': 4,
            'title': 'Grounding Exercise',
            'description': 'Name 5 things you can see, 4 you can touch, 3 you can hear',
            'type': 'anxiety',
            'duration': 3,
            'icon': '🎯'
        })
    
    return recommendations