import streamlit as st
import numpy as np
from scipy.stats import norm
from scipy import optimize
import plotly.graph_objects as go
import time

# --- Page Config ---
st.set_page_config(layout="wide", page_title="Options Analytics Engine")
st.markdown("""
<style>
    .metric-card {
        background-color: #0e1117;
        border: 1px solid #262730;
        border-radius: 5px;
        padding: 15px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- Core Logic Class (Matching Resume OOP/Math) ---
class OptionsPricer:
    def __init__(self, S, K, T, r, sigma, option_type='call'):
        self.S = S
        self.K = K
        self.T = T
        self.r = r
        self.sigma = sigma
        self.type = option_type.lower()

    def _d1_d2(self):
        d1 = (np.log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * np.sqrt(self.T))
        d2 = d1 - self.sigma * np.sqrt(self.T)
        return d1, d2

    def bsm_price(self):
        d1, d2 = self._d1_d2()
        if self.type == 'call':
            price = self.S * norm.cdf(d1) - self.K * np.exp(-self.r * self.T) * norm.cdf(d2)
        else:
            price = self.K * np.exp(-self.r * self.T) * norm.cdf(-d2) - self.S * norm.cdf(-d1)
        return price

    def greeks(self):
        d1, d2 = self._d1_d2()
        
        delta = norm.cdf(d1) if self.type == 'call' else norm.cdf(d1) - 1
        gamma = norm.pdf(d1) / (self.S * self.sigma * np.sqrt(self.T))
        vega = self.S * np.sqrt(self.T) * norm.pdf(d1) # Result is not % scaled usually
        
        theta_part = -(self.S * norm.pdf(d1) * self.sigma) / (2 * np.sqrt(self.T))
        if self.type == 'call':
            theta = theta_part - self.r * self.K * np.exp(-self.r * self.T) * norm.cdf(d2)
            rho = self.K * self.T * np.exp(-self.r * self.T) * norm.cdf(d2)
        else:
            theta = theta_part + self.r * self.K * np.exp(-self.r * self.T) * norm.cdf(-d2)
            rho = -self.K * self.T * np.exp(-self.r * self.T) * norm.cdf(-d2)
            
        return {'Delta': delta, 'Gamma': gamma, 'Theta': theta, 'Vega': vega, 'Rho': rho}

    def monte_carlo_price(self, num_sims=100000):
        """Vectorized Monte Carlo Simulation"""
        # Resume point: "Vectorized NumPy simulation delivered ~10-20x speedup"
        start_time = time.time()
        
        Z = np.random.standard_normal(num_sims)
        dt = self.T
        ST = self.S * np.exp((self.r - 0.5 * self.sigma ** 2) * dt + self.sigma * np.sqrt(dt) * Z)
        
        if self.type == 'call':
            payoffs = np.maximum(ST - self.K, 0)
        else:
            payoffs = np.maximum(self.K - ST, 0)
            
        price = np.exp(-self.r * self.T) * np.mean(payoffs)
        exec_time = time.time() - start_time
        
        return price, exec_time

# --- Sidebar Controls ---
st.sidebar.title("Parameters")
S = st.sidebar.number_input("Spot Price (S)", value=100.0, step=1.0)
K = st.sidebar.number_input("Strike Price (K)", value=100.0, step=1.0)
T = st.sidebar.slider("Time to Maturity (Years)", 0.01, 2.0, 1.0)
r = st.sidebar.slider("Risk-Free Rate (r)", 0.0, 0.1, 0.05)
sigma = st.sidebar.slider("Volatility (σ)", 0.01, 1.5, 0.2)
opt_type = st.sidebar.selectbox("Option Type", ["Call", "Put"])

# --- Main Dashboard ---
st.title("Options Analytics Engine")
st.caption("Powered by NumPy, SciPy, and Streamlit")

# Instantiate Logic
pricer = OptionsPricer(S, K, T, r, sigma, opt_type)

# TABS
tab1, tab2, tab3 = st.tabs(["Pricing & Greeks", "Monte Carlo Analysis", "Volatility Surface"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Analytical Price
        price = pricer.bsm_price()
        greeks = pricer.greeks()
        
        st.metric("BSM Price", f"${price:.4f}")
        for k, v in greeks.items():
            st.metric(k, f"{v:.4f}")

    with col2:
        # HEATMAP: Price vs Spot & Vol
        st.subheader("Price Sensitivity Analysis")
        # Generate grid
        spots = np.linspace(S * 0.5, S * 1.5, 20)
        vols = np.linspace(sigma * 0.5, sigma * 1.5, 20)
        X, Y = np.meshgrid(spots, vols)
        
        # Calculate Z (Price) efficiently
        # Doing loop for clarity, but could be vectorized
        Z = np.zeros_like(X)
        for i in range(len(vols)):
            for j in range(len(spots)):
                p = OptionsPricer(spots[j], K, T, r, vols[i], opt_type)
                Z[i, j] = p.bsm_price()
                
        fig = go.Figure(data=[go.Surface(z=Z, x=spots, y=vols)])
        fig.update_layout(title='Option Price vs Spot & Volatility', autosize=False, height=500,
                          scene=dict(xaxis_title='Spot Price', yaxis_title='Volatility', zaxis_title='Option Price'))
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Monte Carlo Simulation (Vectorized)")
    
    sim_runs = st.slider("Number of Simulations", 1000, 500000, 100000)
    
    if st.button("Run Simulation"):
        mc_price, exec_time = pricer.monte_carlo_price(sim_runs)
        bsm_p = pricer.bsm_price()
        error = abs(mc_price - bsm_p)
        pct_error = (error / bsm_p) * 100 if bsm_p != 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Monte Carlo Price", f"${mc_price:.4f}")
        c2.metric("Execution Time", f"{exec_time:.4f}s")
        c3.metric("% Error vs BSM", f"{pct_error:.4f}%")
        
        # Convergence Plot (Simulating convergence by steps)
        # Check convergence for subset
        ns = np.geomspace(1000, sim_runs, 10).astype(int)
        prices = []
        for n in ns:
            p, _ = pricer.monte_carlo_price(n)
            prices.append(p)
            
        conv_fig = go.Figure()
        conv_fig.add_trace(go.Scatter(x=ns, y=prices, mode='lines+markers', name='MC Price'))
        conv_fig.add_hline(y=bsm_p, line_dash="dash", annotation_text="BSM Theoretical")
        conv_fig.update_xaxes(type="log", title="Number of Paths")
        conv_fig.update_layout(title="Convergence Analysis (Log-Log Scale)")
        st.plotly_chart(conv_fig, use_container_width=True)

with tab3:
    st.subheader("Implied Volatility Solver")
    target_price = st.number_input("Target Option Price", value=float(f"{price:.2f}"), step=0.1)
    
    if st.button("Solve for IV"):
        def objective_func(v_guess):
            # Using Brent's method on Price - Target
            trial_pricer = OptionsPricer(S, K, T, r, v_guess, opt_type)
            return trial_pricer.bsm_price() - target_price
        
        try:
            implied_vol = optimize.brentq(objective_func, 0.001, 5.0)
            st.success(f"Implied Volatility: {implied_vol:.2%}")
        except:
            st.error("Could not converge. Target price might be outside possible arbitrage bounds.")
