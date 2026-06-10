from django.urls import path
from . import views

urlpatterns = [
    path('match/<int:match_id>/', views.match_detail_view, name='match_detail'),
    path('match/<int:match_id>/scorecard/', views.scorecard_view, name='scorecard'),

    # Live scoring
    path('match/<int:match_id>/score/', views.score_view, name='match_score'),
    path('match/<int:match_id>/score/start/', views.start_innings_view, name='start_innings'),
    path('innings/<int:innings_id>/ball/', views.score_ball_view, name='score_ball'),
    path('innings/<int:innings_id>/undo/', views.score_undo_view, name='score_undo'),
    path('innings/<int:innings_id>/batter/', views.score_set_batter_view, name='score_set_batter'),
    path('innings/<int:innings_id>/bowler/', views.score_set_bowler_view, name='score_set_bowler'),
    path('innings/<int:innings_id>/swap-strike/', views.score_swap_strike_view, name='score_swap_strike'),
    path('innings/<int:innings_id>/change-bowler/', views.score_change_bowler_view, name='score_change_bowler'),
    path('innings/<int:innings_id>/overs/', views.score_set_overs_view, name='score_set_overs'),
    path('innings/<int:innings_id>/end/', views.end_innings_view, name='end_innings'),
    path('match/<int:match_id>/reopen/', views.reopen_scoring_view, name='reopen_scoring'),
]
