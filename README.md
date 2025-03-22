1. Clone the Repository

  git clone https://github.com/yourusername/klokreff.git
  cd klokreff

2. Set Up Virtual Environment

  python3 -m venv venv
  source venv/bin/activate  

4. Install Dependencies
  pip install requests web3.py eth-account colorama

5. Prepare Input Files
  refs.txt (Required)
  Create refs.txt in the project root with referral codes or URLs, one per line:
  example : 
  https://klokapp.ai?referral_code=ANOTHERCODE

6. Verify Compatibility
  Check versions to avoid warnings:

  pip show requests urllib3 chardet

  Recommended:
  requests==2.32.3

  urllib3==1.26.18

  chardet==4.0.0
  Pin if needed:

  pip install requests==2.32.3 urllib3==1.26.18 chardet==4.0.0

Usage
  Run the script:

  python start.py

  Enter the number of accounts to generate (max 100 per referral code).

  Monitor progress in the console.

  Output
  Logs: Color-coded updates for each wallet.

  Files: klok_<referral_code>.txt with <private_key>:<address> entries.







