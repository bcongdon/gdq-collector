# Designed to be run on ubuntu 16.04
# NOTE: Do not run this as a script. Meant to be more an "operator's guide"

# Install packages
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install git postgresql postgresql-contrib libpq-dev build-essential python-pip -y

# Setup postgres
sudo service postgresql start

sudo su - postgres

# Setup gdq postgres:
createuser gdqstatus --createdb --password

# Need to change ident -> md5
# Need to add line 'local all postgres peer' to top of file
vim /etc/postgresql/9.5/main/pg_hba.conf

# Need to set "listen_addresses = '*'"
vim /etc/postgresql/9.5/main/postgresql.conf

exit
sudo /etc/init.d/postgresql restart

# Setup gdqstatus user
sudo useradd gdqstatus
sudo usermod -aG sudo gdqstatus
sudo passwd gdqstatus
sudo mkdir /home/gdqstatus
sudo chown -R gdqstatus /home/gdqstatus
sudo cp ~/.bashrc /home/gdqstatus

# Setup gdqstatus database
sudo su - gdqstatus
createdb gdqstatus -U gdqstatus

# Clone gdq collector repo
git clone https://github.com/bcongdon/gdq-collector
cd gdq-collector

# Install dependencies
pip install -r requirements.txt --user --no-cache-dir
mv gdq_collector/credentials_template.py gdq_collector/credentials.py

# Setup postgres tables
psql < schema.sql

# Change
vim pg_hba.conf
