# Designed to be run on ubuntu 16.04
# NOTE: Do not run this as a script. Meant to be more an "operator's guide"

# Install packages
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install git postgresql postgresql-contrib libpq-dev build-essential python-pip awscli unzip libwww-perl libdatetime-perl -y

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

# Setup AWS credentials
aws configure

# Setup EC2 CloudWatch metrics for memory / disk space
curl http://aws-cloudwatch.s3.amazonaws.com/downloads/CloudWatchMonitoringScripts-1.2.1.zip -O
unzip CloudWatchMonitoringScripts-1.2.1.zip
rm CloudWatchMonitoringScripts-1.2.1.zip
cd aws-scripts-mon
mv awscreds.template awscreds.conf
cat <(crontab -l) <(echo "*/5 * * * * ~/aws-scripts-mon/mon-put-instance-data.pl --mem-used-incl-cache-buff --mem-util --disk-space-util --disk-space-avail --disk-space-used --disk-path=/ --from-cron"
) | crontab -

# Enter AWS credentials (can copy keys from ~/.aws/credentials)
vim awscreds.conf
