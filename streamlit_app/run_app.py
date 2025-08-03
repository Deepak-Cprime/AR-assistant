"""
Script to run the Streamlit app
"""
import subprocess
import sys
from pathlib import Path

def run_streamlit_app():
    """Run the Streamlit application"""
    app_path = Path(__file__).parent / "app.py"
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.port", "8501",
            "--server.address", "localhost"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit app: {e}")
    except KeyboardInterrupt:
        print("\nStreamlit app stopped by user")

if __name__ == "__main__":
    run_streamlit_app()