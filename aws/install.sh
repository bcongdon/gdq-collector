sudo yum install git gcc python-setuptools python-devel postgresql-devel -y
git clone https://github.com/bcongdon/agdq-collector
cd agdq-collector
pip install -r requirements.txt --no-cache-dir --user
vim agdq_collector/credentials.py
