import pandas as pd
import numpy as np
import ta
from scipy import stats
from scipy.signal import argrelextrema
import warnings
warnings.filterwarnings('ignore')

class AdvancedIndicators:
    def __init__(self, df):
        self.df = df.copy()
        self.prepare_data()
    
    def prepare_data(self):
        """Prepare and clean data"""
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Calculate typical price and weighted close
        self.df['typical_price'] = (self.df['high'] + self.df['low'] + self.df['close']) / 3
        self.df['weighted_close'] = (self.df['high'] + self.df['low'] + 2*self.df['close']) / 4
    
    def momentum_indicators(self):
        """Advanced momentum indicators"""
        close = self.df['close']
        high = self.df['high']
        low = self.df['low']
        volume = self.df['volume']
        
        # RSI family
        self.df['rsi_14'] = ta.momentum.RSIIndicator(close, window=14).rsi()
        self.df['rsi_21'] = ta.momentum.RSIIndicator(close, window=21).rsi()
        self.df['rsi_50'] = ta.momentum.RSIIndicator(close, window=50).rsi()
        
        # Stochastic family
        stoch = ta.momentum.StochasticOscillator(high, low, close)
        self.df['stoch_k'] = stoch.stoch()
        self.df['stoch_d'] = stoch.stoch_signal()
        
        # MACD family
        macd = ta.trend.MACD(close)
        self.df['macd'] = macd.macd()
        self.df['macd_signal'] = macd.macd_signal()
        self.df['macd_diff'] = macd.macd_diff()
        
        # Williams %R
        self.df['williams_r'] = ta.momentum.WilliamsRIndicator(high, low, close).williams_r()
        
        # Rate of Change
        self.df['roc_10'] = ta.momentum.ROCIndicator(close, window=10).roc()
        self.df['roc_20'] = ta.momentum.ROCIndicator(close, window=20).roc()
        
        # Commodity Channel Index
        self.df['cci'] = ta.trend.CCIIndicator(high, low, close).cci()
        
        # Money Flow Index
        self.df['mfi'] = ta.volume.MFIIndicator(high, low, close, volume).money_flow_index()
        
        # Ultimate Oscillator
        self.df['uo'] = ta.momentum.UltimateOscillator(high, low, close).ultimate_oscillator()
        
        # Awesome Oscillator
        self.df['ao'] = ta.momentum.AwesomeOscillatorIndicator(high, low).awesome_oscillator()
    
    def trend_indicators(self):
        """Advanced trend indicators"""
        close = self.df['close']
        high = self.df['high']
        low = self.df['low']
        
        # EMA family
        for period in [5, 8, 13, 21, 34, 50, 89, 144, 200]:
            self.df[f'ema_{period}'] = ta.trend.EMAIndicator(close, window=period).ema_indicator()
        
        # SMA family
        for period in [10, 20, 50, 100, 200]:
            self.df[f'sma_{period}'] = ta.trend.SMAIndicator(close, window=period).sma_indicator()
        
        # ADX - Average Directional Index
        adx = ta.trend.ADXIndicator(high, low, close)
        self.df['adx'] = adx.adx()
        self.df['adx_pos'] = adx.adx_pos()
        self.df['adx_neg'] = adx.adx_neg()
        
        # Aroon
        # aroon = ta.trend.AroonIndicator(high=high, low=low, close=close)
        # self.df['aroon_up'] = aroon.aroon_up()
        # self.df['aroon_down'] = aroon.aroon_down()
        # self.df['aroon_ind'] = aroon.aroon_indicator()
        
        # PSAR - Parabolic SAR
        self.df['psar'] = ta.trend.PSARIndicator(high, low, close).psar()
        
        # Ichimoku Cloud
        ichimoku = ta.trend.IchimokuIndicator(high, low)
        self.df['ichimoku_a'] = ichimoku.ichimoku_a()
        self.df['ichimoku_b'] = ichimoku.ichimoku_b()
        self.df['ichimoku_base'] = ichimoku.ichimoku_base_line()
        self.df['ichimoku_conv'] = ichimoku.ichimoku_conversion_line()
        
        # Trix
        self.df['trix'] = ta.trend.TRIXIndicator(close).trix()
    
    def volatility_indicators(self):
        """Advanced volatility indicators"""
        close = self.df['close']
        high = self.df['high']
        low = self.df['low']
        
        # Bollinger Bands family
        for period in [14, 20, 50]:
            bb = ta.volatility.BollingerBands(close, window=period)
            self.df[f'bb_upper_{period}'] = bb.bollinger_hband()
            self.df[f'bb_middle_{period}'] = bb.bollinger_mavg()
            self.df[f'bb_lower_{period}'] = bb.bollinger_lband()
            self.df[f'bb_width_{period}'] = bb.bollinger_wband()
            self.df[f'bb_pband_{period}'] = bb.bollinger_pband()
        
        # Average True Range
        self.df['atr_14'] = ta.volatility.AverageTrueRange(high, low, close).average_true_range()
        
        # Keltner Channel
        kc = ta.volatility.KeltnerChannel(high, low, close)
        self.df['kc_upper'] = kc.keltner_channel_hband()
        self.df['kc_middle'] = kc.keltner_channel_mband()
        self.df['kc_lower'] = kc.keltner_channel_lband()
        
        # Donchian Channel
        dc = ta.volatility.DonchianChannel(high, low, close)
        self.df['dc_upper'] = dc.donchian_channel_hband()
        self.df['dc_middle'] = dc.donchian_channel_mband()
        self.df['dc_lower'] = dc.donchian_channel_lband()
        
        # Ulcer Index
        self.df['ui'] = ta.volatility.UlcerIndex(close).ulcer_index()
    
    def volume_indicators(self):
        """Advanced volume indicators"""
        close = self.df['close']
        high = self.df['high']
        low = self.df['low']
        volume = self.df['volume']
        
        # Volume SMAs
        for period in [10, 20, 50]:
            self.df[f'volume_sma_{period}'] = volume.rolling(period, min_periods=1).mean()
        
        # On Balance Volume
        self.df['obv'] = ta.volume.OnBalanceVolumeIndicator(close, volume).on_balance_volume()
        
        # Accumulation Distribution Line
        self.df['ad'] = ta.volume.AccDistIndexIndicator(high, low, close, volume).acc_dist_index()
        
        # Chaikin Money Flow
        self.df['cmf'] = ta.volume.ChaikinMoneyFlowIndicator(high, low, close, volume).chaikin_money_flow()
        
        # Volume Price Trend
        self.df['vpt'] = ta.volume.VolumePriceTrendIndicator(close, volume).volume_price_trend()
        
        # Ease of Movement
        self.df['eom'] = ta.volume.EaseOfMovementIndicator(high, low, volume).ease_of_movement()
        
        # Volume Weighted Average Price
        self.df['vwap'] = (close * volume).cumsum() / volume.cumsum()
        
        # Negative Volume Index
        self.df['nvi'] = ta.volume.NegativeVolumeIndexIndicator(close, volume).negative_volume_index()
    
    def custom_indicators(self):
        """Custom advanced indicators"""
        close = self.df['close']
        high = self.df['high']
        low = self.df['low']
        volume = self.df['volume']
        
        # Price momentum
        self.df['momentum_10'] = close / close.shift(10) - 1
        self.df['momentum_20'] = close / close.shift(20) - 1
        
        # Volatility measures
        self.df['volatility_10'] = close.rolling(10, min_periods=1).std()
        self.df['volatility_20'] = close.rolling(20, min_periods=1).std()
        
        # Price position in range
        self.df['price_position'] = (close - low.rolling(14).min()) / (high.rolling(14).max() - low.rolling(14).min())
        
        # Volume momentum
        self.df['volume_momentum'] = volume / volume.rolling(20, min_periods=1).mean()
        
        # High-Low spread
        self.df['hl_spread'] = (high - low) / close
        
        # Price acceleration
        self.df['price_acceleration'] = close.diff().diff()
        
        # Trend strength
        self.df['trend_strength'] = abs(close.rolling(20, min_periods=1).apply(lambda x: stats.linregress(range(len(x)), x)[0] if len(x) > 1 else 0))
        
        # Support/Resistance levels
        self.calculate_support_resistance()
        
        # Market regime
        self.df['market_regime'] = self.classify_market_regime()
    
    def calculate_support_resistance(self):
        """Calculate dynamic support and resistance levels"""
        close = self.df['close']
        high = self.df['high']
        low = self.df['low']
        
        # Find local minima and maxima
        local_min = argrelextrema(low.values, np.less, order=5)[0]
        local_max = argrelextrema(high.values, np.greater, order=5)[0]
        
        # Initialize support and resistance columns
        self.df['support'] = np.nan
        self.df['resistance'] = np.nan
        
        # Calculate support levels
        if len(local_min) > 0:
            recent_lows = low.iloc[local_min[-min(5, len(local_min)):]]
            support_level = recent_lows.mean()
            self.df['support'] = support_level
        
        # Calculate resistance levels
        if len(local_max) > 0:
            recent_highs = high.iloc[local_max[-min(5, len(local_max)):]]
            resistance_level = recent_highs.mean()
            self.df['resistance'] = resistance_level
    
    def classify_market_regime(self):
        """Classify market regime (trending/ranging)"""
        close = self.df['close']
        
        # Calculate 20-period linear regression slope
        def get_slope(series):
            if len(series) < 2:
                return 0
            x = np.arange(len(series))
            slope, _, r_value, _, _ = stats.linregress(x, series)
            return slope * r_value**2  # Adjust by R-squared
        
        slopes = close.rolling(20, min_periods=1).apply(get_slope)
        
        # Classify regime
        regime = np.where(slopes > 0.01, 1,  # Uptrend
                 np.where(slopes < -0.01, -1, 0))  # Downtrend, Sideways
        
        return regime
    
    def pattern_recognition(self):
        """Candlestick pattern recognition"""
        open_price = self.df['open']
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        # Doji patterns
        body = abs(close - open_price)
        body_pct = body / close
        self.df['doji'] = body_pct < 0.001
        
        # Hammer and Hanging Man
        lower_shadow = np.where(close > open_price, open_price - low, close - low)
        upper_shadow = np.where(close > open_price, high - close, high - open_price)
        body_size = abs(close - open_price)
        
        self.df['hammer'] = (lower_shadow > 2 * body_size) & (upper_shadow < 0.1 * body_size)
        self.df['hanging_man'] = self.df['hammer']  # Same pattern, different context
        
        # Shooting Star and Inverted Hammer
        self.df['shooting_star'] = (upper_shadow > 2 * body_size) & (lower_shadow < 0.1 * body_size)
        self.df['inverted_hammer'] = self.df['shooting_star']
        
        # Engulfing patterns
        prev_body = abs(close.shift(1) - open_price.shift(1))
        curr_body = abs(close - open_price)
        
        bullish_engulfing = (close.shift(1) < open_price.shift(1)) & (close > open_price) & \
                           (open_price < close.shift(1)) & (close > open_price.shift(1)) & \
                           (curr_body > prev_body)
        
        bearish_engulfing = (close.shift(1) > open_price.shift(1)) & (close < open_price) & \
                           (open_price > close.shift(1)) & (close < open_price.shift(1)) & \
                           (curr_body > prev_body)
        
        self.df['bullish_engulfing'] = bullish_engulfing
        self.df['bearish_engulfing'] = bearish_engulfing
        
        # Morning Star and Evening Star (simplified 3-candle patterns)
        self.df['morning_star'] = self.detect_morning_star()
        self.df['evening_star'] = self.detect_evening_star()
    
    def detect_morning_star(self):
        """Detect Morning Star pattern"""
        close = self.df['close']
        open_price = self.df['open']
        
        # Simplified morning star detection
        cond1 = close.shift(2) < open_price.shift(2)  # First candle bearish
        cond2 = abs(close.shift(1) - open_price.shift(1)) < abs(close.shift(2) - open_price.shift(2)) * 0.3  # Small body
        cond3 = close > open_price  # Third candle bullish
        cond4 = close > (close.shift(2) + open_price.shift(2)) / 2  # Close above midpoint of first candle
        
        return cond1 & cond2 & cond3 & cond4
    
    def detect_evening_star(self):
        """Detect Evening Star pattern"""
        close = self.df['close']
        open_price = self.df['open']
        
        # Simplified evening star detection
        cond1 = close.shift(2) > open_price.shift(2)  # First candle bullish
        cond2 = abs(close.shift(1) - open_price.shift(1)) < abs(close.shift(2) - open_price.shift(2)) * 0.3  # Small body
        cond3 = close < open_price  # Third candle bearish
        cond4 = close < (close.shift(2) + open_price.shift(2)) / 2  # Close below midpoint of first candle
        
        return cond1 & cond2 & cond3 & cond4
    
    def fibonacci_levels(self):
        """Calculate Fibonacci retracement levels"""
        high = self.df['high']
        low = self.df['low']
        
        # Find recent swing high and low
        swing_high = high.rolling(20, min_periods=1).max().iloc[-1]
        swing_low = low.rolling(20, min_periods=1).min().iloc[-1]
        
        # Calculate Fibonacci levels
        diff = swing_high - swing_low
        
        fib_levels = {
            'fib_0': swing_high,
            'fib_236': swing_high - 0.236 * diff,
            'fib_382': swing_high - 0.382 * diff,
            'fib_500': swing_high - 0.500 * diff,
            'fib_618': swing_high - 0.618 * diff,
            'fib_786': swing_high - 0.786 * diff,
            'fib_100': swing_low
        }
        
        for level, value in fib_levels.items():
            self.df[level] = value
    
    def compute_all_indicators(self):
        print("📊 计算指标中...")
        """Compute all indicators and return analysis"""
        self.momentum_indicators()
        self.trend_indicators()
        self.volatility_indicators()
        self.volume_indicators()
        self.custom_indicators()
        self.pattern_recognition()
        self.fibonacci_levels()
        
        # Drop rows with NaN values
        self.df = self.df.dropna()
        
        if len(self.df) == 0:
            return None
        
        # Return the latest row with additional analysis
        latest = self.df.iloc[-1]
        
        # Add comprehensive analysis
        analysis = self.generate_comprehensive_analysis(latest)
        
        return latest, analysis, self.df
    
    def generate_comprehensive_analysis(self, latest):
        """Generate comprehensive market analysis"""
        analysis = {
            'trend_analysis': self.analyze_trend(latest),
            'momentum_analysis': self.analyze_momentum(latest),
            'volatility_analysis': self.analyze_volatility(latest),
            'volume_analysis': self.analyze_volume(latest),
            'pattern_analysis': self.analyze_patterns(latest),
            'support_resistance': self.analyze_support_resistance(latest),
            'overall_signal': None
        }
        
        # Generate overall signal
        analysis['overall_signal'] = self.generate_overall_signal(analysis)
        
        return analysis
    
    def analyze_trend(self, latest):
        """Analyze trend indicators"""
        trend_score = 0
        signals = []
        
        # EMA crossovers
        if latest['ema_8'] > latest['ema_21']:
            trend_score += 1
            signals.append("EMA 8 > EMA 21 (Bullish)")
        else:
            trend_score -= 1
            signals.append("EMA 8 < EMA 21 (Bearish)")
        
        if latest['ema_21'] > latest['ema_50']:
            trend_score += 1
            signals.append("EMA 21 > EMA 50 (Bullish)")
        else:
            trend_score -= 1
            signals.append("EMA 21 < EMA 50 (Bearish)")
        
        # ADX strength
        if latest['adx'] > 25:
            signals.append(f"Strong trend (ADX: {latest['adx']:.1f})")
            if latest['adx_pos'] > latest['adx_neg']:
                trend_score += 1
                signals.append("Bullish ADX direction")
            else:
                trend_score -= 1
                signals.append("Bearish ADX direction")
        else:
            signals.append(f"Weak trend (ADX: {latest['adx']:.1f})")
        
        # Market regime
        if latest['market_regime'] == 1:
            trend_score += 2
            signals.append("Uptrending market regime")
        elif latest['market_regime'] == -1:
            trend_score -= 2
            signals.append("Downtrending market regime")
        else:
            signals.append("Sideways market regime")
        
        return {
            'score': trend_score,
            'signals': signals,
            'strength': 'Strong' if abs(trend_score) >= 3 else 'Moderate' if abs(trend_score) >= 1 else 'Weak'
        }
    
    def analyze_momentum(self, latest):
        """Analyze momentum indicators"""
        momentum_score = 0
        signals = []
        
        # RSI analysis
        rsi = latest['rsi_14']
        if rsi > 70:
            momentum_score -= 1
            signals.append(f"RSI overbought ({rsi:.1f})")
        elif rsi < 30:
            momentum_score += 1
            signals.append(f"RSI oversold ({rsi:.1f})")
        else:
            signals.append(f"RSI neutral ({rsi:.1f})")
        
        # MACD analysis
        if latest['macd'] > latest['macd_signal']:
            momentum_score += 1
            signals.append("MACD bullish crossover")
        else:
            momentum_score -= 1
            signals.append("MACD bearish crossover")
        
        # Stochastic analysis
        if latest['stoch_k'] > 80:
            momentum_score -= 1
            signals.append("Stochastic overbought")
        elif latest['stoch_k'] < 20:
            momentum_score += 1
            signals.append("Stochastic oversold")
        
        # Williams %R
        if latest['williams_r'] > -20:
            momentum_score -= 1
            signals.append("Williams %R overbought")
        elif latest['williams_r'] < -80:
            momentum_score += 1
            signals.append("Williams %R oversold")
        
        return {
            'score': momentum_score,
            'signals': signals,
            'strength': 'Strong' if abs(momentum_score) >= 3 else 'Moderate' if abs(momentum_score) >= 1 else 'Weak'
        }
    
    def analyze_volatility(self, latest):
        """Analyze volatility indicators"""
        signals = []
        
        # Bollinger Bands
        bb_position = latest['bb_pband_20']
        if bb_position > 0.8:
            signals.append("Price near upper Bollinger Band")
        elif bb_position < 0.2:
            signals.append("Price near lower Bollinger Band")
        else:
            signals.append("Price within Bollinger Bands")
        
        # ATR analysis
        atr = latest['atr_14']
        volatility_level = "High" if atr > latest['close'] * 0.03 else "Normal"
        signals.append(f"Volatility: {volatility_level} (ATR: {atr:.2f})")
        
        return {
            'signals': signals,
            'bb_position': bb_position,
            'atr': atr
        }
    
    def analyze_volume(self, latest):
        """Analyze volume indicators"""
        volume_score = 0
        signals = []
        
        # Volume momentum
        vol_momentum = latest['volume_momentum']
        if vol_momentum > 1.5:
            volume_score += 1
            signals.append(f"High volume activity ({vol_momentum:.1f}x average)")
        elif vol_momentum < 0.5:
            volume_score -= 1
            signals.append(f"Low volume activity ({vol_momentum:.1f}x average)")
        
        # OBV trend
        # Note: This would require comparing with previous values
        signals.append("OBV analysis requires historical comparison")
        
        return {
            'score': volume_score,
            'signals': signals
        }
    
    def analyze_patterns(self, latest):
        """Analyze candlestick patterns"""
        patterns = []
        
        if latest['doji']:
            patterns.append("Doji - Indecision")
        if latest['hammer']:
            patterns.append("Hammer - Potential reversal")
        if latest['shooting_star']:
            patterns.append("Shooting Star - Potential reversal")
        if latest['bullish_engulfing']:
            patterns.append("Bullish Engulfing - Strong bullish signal")
        if latest['bearish_engulfing']:
            patterns.append("Bearish Engulfing - Strong bearish signal")
        if latest['morning_star']:
            patterns.append("Morning Star - Bullish reversal")
        if latest['evening_star']:
            patterns.append("Evening Star - Bearish reversal")
        
        return {
            'patterns': patterns if patterns else ['No significant patterns detected']
        }
    
    def analyze_support_resistance(self, latest):
        """Analyze support and resistance levels"""
        current_price = latest['close']
        support = latest['support']
        resistance = latest['resistance']
        
        analysis = {
            'current_price': current_price,
            'support': support,
            'resistance': resistance,
            'distance_to_support': ((current_price - support) / current_price * 100) if not pd.isna(support) else None,
            'distance_to_resistance': ((resistance - current_price) / current_price * 100) if not pd.isna(resistance) else None
        }
        
        return analysis
    
    def generate_overall_signal(self, analysis):
        """Generate overall trading signal"""
        total_score = 0
        confidence = 0
        
        # Weight different analyses
        total_score += analysis['trend_analysis']['score'] * 0.4
        total_score += analysis['momentum_analysis']['score'] * 0.3
        total_score += analysis['volume_analysis']['score'] * 0.2
        
        # Adjust for patterns
        patterns = analysis['pattern_analysis']['patterns']
        if any('bullish' in p.lower() for p in patterns):
            total_score += 1
        if any('bearish' in p.lower() for p in patterns):
            total_score -= 1
        
        # Calculate confidence based on agreement between indicators
        trend_strength = analysis['trend_analysis']['strength']
        momentum_strength = analysis['momentum_analysis']['strength']
        
        if trend_strength == 'Strong' and momentum_strength == 'Strong':
            confidence = min(90, abs(total_score) * 15 + 60)
        elif trend_strength in ['Strong', 'Moderate'] or momentum_strength in ['Strong', 'Moderate']:
            confidence = min(75, abs(total_score) * 12 + 45)
        else:
            confidence = min(60, abs(total_score) * 10 + 30)
        
        # Generate signal
        if total_score > 1.5:
            signal = "STRONG BUY"
        elif total_score > 0.5:
            signal = "BUY"
        elif total_score > -0.5:
            signal = "WAIT"
        elif total_score > -1.5:
            signal = "SELL"
        else:
            signal = "STRONG SELL"
        
        return {
            'signal': signal,
            'score': total_score,
            'confidence': confidence
        }

def compute_indicators(df):
    """Main function to compute all indicators"""
    try:
        indicator_system = AdvancedIndicators(df)
        result = indicator_system.compute_all_indicators()
        
        if result is None:
            return None, None, None
        
        latest, analysis, full_df = result
        return latest, analysis, full_df
    
    except Exception as e:
        import traceback
        print(f"Error computing indicators: {e}")
        print(traceback.format_exc())
        return None, None, None