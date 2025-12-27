# Options Analytics Engine (Python)

A high-performance Options Pricing and Analytics tool built with **Python**, **Streamlit**, **NumPy**, and **SciPy**.

## Features
- **Black-Scholes-Merton Pricing**: European Call/Put pricing with Greeks (Delta, Gamma, Vega, Theta, Rho).
- **Vectorized Monte Carlo**: High-speed simulation of 100,000+ price paths using NumPy.
- **Implied Volatility Solver**: Numerical solver (Brent's method) to pivot volatility from market price.
- **Interactive Volatility Surface**: 3D visualization of option sensitivities.

## Quick Start
1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Run the app:
    ```bash
    streamlit run app.py
    ```

## Tech Stack
-   Frontend: [Streamlit](https://streamlit.io/)
-   Math: [NumPy](https://numpy.org/), [SciPy](https://scipy.org/)
-   Visualization: [Plotly](https://plotly.com/)
