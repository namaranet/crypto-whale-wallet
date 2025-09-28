#!/usr/bin/env python3
"""
Test-Driven Development Tests for Profitable Whale Trader Detection System
Tests for trading session detection, profitability analysis, and pattern recognition
"""

import unittest
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sqlite3
import tempfile
import os


class TestTradingSessionDetection(unittest.TestCase):
    """Test trading session grouping and detection algorithms"""
    
    def setUp(self):
        """Set up test data for trading session detection"""
        self.sample_transactions = [
            # Profitable WETH trading session
            {
                'hash': '0xabc123',
                'from_address': '0x1234567890123456789012345678901234567890',
                'to_address': '0xdead567890123456789012345678901234567890',
                'token_symbol': 'WETH',
                'token_address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                'value_native': 50.0,  # 50 WETH
                'value_usd': 150000.0,  # $150K USD (entry at $3000/WETH)
                'timestamp': int((datetime.now() - timedelta(days=10)).timestamp()),
                'transaction_type': 'buy'
            },
            {
                'hash': '0xdef456',
                'from_address': '0xdead567890123456789012345678901234567890',
                'to_address': '0x1234567890123456789012345678901234567890',
                'token_symbol': 'WETH',
                'token_address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                'value_native': 50.0,  # 50 WETH
                'value_usd': 175000.0,  # $175K USD (exit at $3500/WETH)
                'timestamp': int((datetime.now() - timedelta(days=5)).timestamp()),
                'transaction_type': 'sell'
            },
            # Losing USDC trading session
            {
                'hash': '0xghi789',
                'from_address': '0x1234567890123456789012345678901234567890',
                'to_address': '0xbeef567890123456789012345678901234567890',
                'token_symbol': 'UNI',
                'token_address': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',
                'value_native': 10000.0,  # 10K UNI
                'value_usd': 120000.0,  # $120K USD (entry at $12/UNI)
                'timestamp': int((datetime.now() - timedelta(days=15)).timestamp()),
                'transaction_type': 'buy'
            },
            {
                'hash': '0xjkl012',
                'from_address': '0xbeef567890123456789012345678901234567890',
                'to_address': '0x1234567890123456789012345678901234567890',
                'token_symbol': 'UNI',
                'token_address': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',
                'value_native': 10000.0,  # 10K UNI
                'value_usd': 100000.0,  # $100K USD (exit at $10/UNI)
                'timestamp': int((datetime.now() - timedelta(days=8)).timestamp()),
                'transaction_type': 'sell'
            }
        ]
    
    def test_group_transactions_into_sessions(self):
        """Test that transactions are correctly grouped into trading sessions by token"""
        from profitable_trader_analyzer import TradingSessionDetector
        
        detector = TradingSessionDetector()
        sessions = detector.group_transactions_into_sessions(self.sample_transactions)
        
        # Should have 2 sessions (WETH and UNI)
        self.assertEqual(len(sessions), 2)
        
        # Check WETH session
        weth_session = next(s for s in sessions if s.token_symbol == 'WETH')
        self.assertEqual(weth_session.token_symbol, 'WETH')
        self.assertEqual(len(weth_session.entry_transactions), 1)
        self.assertEqual(len(weth_session.exit_transactions), 1)
        self.assertEqual(weth_session.total_invested, 150000.0)
        self.assertEqual(weth_session.total_received, 175000.0)
        
        # Check UNI session
        uni_session = next(s for s in sessions if s.token_symbol == 'UNI')
        self.assertEqual(uni_session.token_symbol, 'UNI')
        self.assertEqual(uni_session.total_invested, 120000.0)
        self.assertEqual(uni_session.total_received, 100000.0)
    
    def test_calculate_session_profitability(self):
        """Test profit/loss calculation for trading sessions"""
        from profitable_trader_analyzer import TradingSession
        
        # Profitable session
        profitable_session = TradingSession(
            token_symbol='WETH',
            total_invested=150000.0,
            total_received=175000.0,
            entry_timestamp=int((datetime.now() - timedelta(days=10)).timestamp()),
            exit_timestamp=int((datetime.now() - timedelta(days=5)).timestamp())
        )
        
        self.assertEqual(profitable_session.profit_loss, 25000.0)
        self.assertAlmostEqual(profitable_session.profit_percentage, 16.67, places=2)
        self.assertEqual(profitable_session.hold_duration.days, 5)
        self.assertTrue(profitable_session.is_profitable)
        
        # Losing session
        losing_session = TradingSession(
            token_symbol='UNI',
            total_invested=120000.0,
            total_received=100000.0,
            entry_timestamp=int((datetime.now() - timedelta(days=15)).timestamp()),
            exit_timestamp=int((datetime.now() - timedelta(days=8)).timestamp())
        )
        
        self.assertEqual(losing_session.profit_loss, -20000.0)
        self.assertAlmostEqual(losing_session.profit_percentage, -16.67, places=2)
        self.assertFalse(losing_session.is_profitable)
    
    def test_minimum_volume_threshold(self):
        """Test that only sessions >$100K are analyzed"""
        from profitable_trader_analyzer import TradingSessionDetector
        
        small_transactions = [
            {
                'token_symbol': 'PEPE',
                'value_usd': 50000.0,  # Below $100K threshold
                'transaction_type': 'buy'
            }
        ]
        
        detector = TradingSessionDetector(min_volume_usd=100000)
        sessions = detector.group_transactions_into_sessions(small_transactions)
        
        # Should be empty due to volume filter
        self.assertEqual(len(sessions), 0)


class TestProfitabilityScoring(unittest.TestCase):
    """Test profitability scoring and trader ranking algorithms"""
    
    def setUp(self):
        """Set up test trading sessions for scoring"""
        self.sample_sessions = [
            # Elite trader - 4 wins, 1 loss
            {
                'wallet_address': '0xelite123',
                'sessions': [
                    {'profit_loss': 25000, 'profit_percentage': 16.67, 'volume': 150000},
                    {'profit_loss': 50000, 'profit_percentage': 25.0, 'volume': 200000},
                    {'profit_loss': 30000, 'profit_percentage': 20.0, 'volume': 150000},
                    {'profit_loss': 75000, 'profit_percentage': 30.0, 'volume': 250000},
                    {'profit_loss': -15000, 'profit_percentage': -10.0, 'volume': 150000}
                ]
            },
            # Average trader - 2 wins, 2 losses
            {
                'wallet_address': '0xaverage456',
                'sessions': [
                    {'profit_loss': 10000, 'profit_percentage': 8.33, 'volume': 120000},
                    {'profit_loss': -8000, 'profit_percentage': -6.67, 'volume': 120000},
                    {'profit_loss': 15000, 'profit_percentage': 12.5, 'volume': 120000},
                    {'profit_loss': -12000, 'profit_percentage': -10.0, 'volume': 120000}
                ]
            }
        ]
    
    def test_calculate_trader_profitability_score(self):
        """Test overall profitability scoring algorithm"""
        from profitable_trader_analyzer import ProfitabilityScorer
        
        scorer = ProfitabilityScorer()
        
        # Elite trader scoring
        elite_sessions = self.sample_sessions[0]['sessions']
        elite_score = scorer.calculate_trader_score('0xelite123', elite_sessions)
        
        self.assertGreater(elite_score, 800)  # Should be high score
        self.assertLess(elite_score, 1000)    # But not perfect
        
        # Average trader scoring
        avg_sessions = self.sample_sessions[1]['sessions']
        avg_score = scorer.calculate_trader_score('0xaverage456', avg_sessions)
        
        self.assertGreater(avg_score, 400)    # Should be moderate score
        self.assertLess(avg_score, 700)       # But not high
        
        # Elite should score higher than average
        self.assertGreater(elite_score, avg_score)
    
    def test_win_rate_calculation(self):
        """Test win rate percentage calculation"""
        from profitable_trader_analyzer import ProfitabilityScorer
        
        scorer = ProfitabilityScorer()
        
        # Elite trader: 4 wins out of 5 = 80%
        elite_sessions = self.sample_sessions[0]['sessions']
        elite_metrics = scorer.calculate_performance_metrics(elite_sessions)
        self.assertEqual(elite_metrics['win_rate'], 0.8)
        
        # Average trader: 2 wins out of 4 = 50%
        avg_sessions = self.sample_sessions[1]['sessions']
        avg_metrics = scorer.calculate_performance_metrics(avg_sessions)
        self.assertEqual(avg_metrics['win_rate'], 0.5)
    
    def test_total_profit_calculation(self):
        """Test total realized profit calculation"""
        from profitable_trader_analyzer import ProfitabilityScorer
        
        scorer = ProfitabilityScorer()
        
        # Elite trader total: 25000 + 50000 + 30000 + 75000 - 15000 = 165000
        elite_sessions = self.sample_sessions[0]['sessions']
        elite_metrics = scorer.calculate_performance_metrics(elite_sessions)
        self.assertEqual(elite_metrics['total_profit'], 165000)
        
        # Average trader total: 10000 - 8000 + 15000 - 12000 = 5000
        avg_sessions = self.sample_sessions[1]['sessions']
        avg_metrics = scorer.calculate_performance_metrics(avg_sessions)
        self.assertEqual(avg_metrics['total_profit'], 5000)
    
    def test_trader_tier_classification(self):
        """Test trader tier classification based on performance"""
        from profitable_trader_analyzer import ProfitabilityScorer
        
        scorer = ProfitabilityScorer()
        
        # Elite tier: >$100K profit + >70% win rate
        elite_sessions = self.sample_sessions[0]['sessions']
        elite_tier = scorer.classify_trader_tier(elite_sessions)
        self.assertEqual(elite_tier, 'ELITE')
        
        # Emerging tier: <$100K profit
        avg_sessions = self.sample_sessions[1]['sessions']
        avg_tier = scorer.classify_trader_tier(avg_sessions)
        self.assertEqual(avg_tier, 'EMERGING')


class TestHistoricalPriceIntegration(unittest.TestCase):
    """Test historical price data integration for accurate P&L calculation"""
    
    def test_price_lookup_at_transaction_time(self):
        """Test fetching historical price data for specific timestamps"""
        from profitable_trader_analyzer import HistoricalPriceProvider
        
        provider = HistoricalPriceProvider()
        
        # Test WETH price lookup
        test_timestamp = int((datetime.now() - timedelta(days=1)).timestamp())
        weth_price = provider.get_price_at_timestamp(
            '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH
            test_timestamp
        )
        
        self.assertIsNotNone(weth_price)
        self.assertGreater(weth_price, 1000)  # WETH should be >$1000
        self.assertLess(weth_price, 10000)    # But <$10000
    
    def test_profit_calculation_with_real_prices(self):
        """Test P&L calculation using real historical prices"""
        from profitable_trader_analyzer import TradingSession, HistoricalPriceProvider
        
        provider = HistoricalPriceProvider()
        
        entry_time = int((datetime.now() - timedelta(days=10)).timestamp())
        exit_time = int((datetime.now() - timedelta(days=5)).timestamp())
        
        # Create session with real price lookup
        session = TradingSession(
            token_symbol='WETH',
            token_address='0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
            entry_timestamp=entry_time,
            exit_timestamp=exit_time,
            volume_native=100.0  # 100 WETH
        )
        
        session.calculate_pnl_with_real_prices(provider)
        
        self.assertIsNotNone(session.entry_price)
        self.assertIsNotNone(session.exit_price)
        self.assertIsNotNone(session.profit_loss)
        self.assertIsNotNone(session.profit_percentage)


class TestPatternRecognition(unittest.TestCase):
    """Test trading pattern recognition and strategy classification"""
    
    def test_dip_buying_pattern_detection(self):
        """Test detection of dip buying strategy"""
        from profitable_trader_analyzer import PatternAnalyzer
        
        analyzer = PatternAnalyzer()
        
        # Mock sessions showing dip buying (entries during price drops)
        dip_buying_sessions = [
            {
                'entry_timestamp': 1640995200,  # Entry during market dip
                'market_movement_at_entry': -15.2,  # 15% drop
                'profit_percentage': 25.0,
                'hold_duration_days': 7
            },
            {
                'entry_timestamp': 1641081600,
                'market_movement_at_entry': -8.5,   # 8.5% drop
                'profit_percentage': 18.0,
                'hold_duration_days': 5
            }
        ]
        
        pattern = analyzer.detect_trading_pattern(dip_buying_sessions)
        self.assertEqual(pattern['primary_strategy'], 'DIP_BUYER')
        self.assertGreater(pattern['confidence'], 0.7)
    
    def test_swing_trading_pattern_detection(self):
        """Test detection of swing trading strategy"""
        from profitable_trader_analyzer import PatternAnalyzer
        
        analyzer = PatternAnalyzer()
        
        # Mock sessions showing swing trading (2-30 day holds)
        swing_sessions = [
            {
                'hold_duration_days': 14,
                'profit_percentage': 12.0,
                'entry_timing': 'neutral_market'
            },
            {
                'hold_duration_days': 21,
                'profit_percentage': 8.5,
                'entry_timing': 'neutral_market'
            },
            {
                'hold_duration_days': 7,
                'profit_percentage': 15.0,
                'entry_timing': 'neutral_market'
            }
        ]
        
        pattern = analyzer.detect_trading_pattern(swing_sessions)
        self.assertEqual(pattern['primary_strategy'], 'SWING_TRADER')
        self.assertGreater(pattern['avg_hold_days'], 5)
        self.assertLess(pattern['avg_hold_days'], 35)


if __name__ == '__main__':
    unittest.main()