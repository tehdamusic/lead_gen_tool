from setuptools import setup, find_packages

setup(
    name="lead_gen",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        # Web scraping
        "selenium>=4.15.2",
        "webdriver-manager>=4.0.1",
        "beautifulsoup4>=4.12.2",
        "requests>=2.31.0",
        
        # API clients
        "openai>=1.3.8",
        "google-api-python-client>=2.108.0",
        "google-auth-httplib2>=0.1.1",
        "google-auth-oauthlib>=1.1.0",
        "gspread>=5.12.0",
        
        # Data processing
        "pandas>=2.1.3",
        "numpy>=1.26.2",
        
        # Environment
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "lead-gen=lead_gen.__main__:main",
        ],
    },
)
