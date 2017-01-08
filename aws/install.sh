sudo yum install git tmux gcc python-setuptools python-devel postgresql-devel -y
git clone https://github.com/bcongdon/gdq-collector
cd gdq-collector
pip install -r requirements.txt --no-cache-dir --user
vim gdq_collector/credentials.py
