# Designed to be run on ubuntu 20.04
# NOTE: Do not run this as a script. Meant to be more an "operator's guide"

# Install packages
sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt-get install git postgresql postgresql-contrib libpq-dev build-essential python3-pip awscli unzip libwww-perl libdatetime-perl -y
sudo pip3 install pipenv

# Setup gdqstatus user
sudo useradd -m gdqstatus
sudo usermod -aG sudo gdqstatus
sudo passwd gdqstatus

# Setup gdqstatus database (No longer necessary as the db has been dockerized)
# sudo -u postgres createuser -U postgres -s gdqstatus
# sudo -u postgres createdb gdqstatus -U gdqstatus
# sudo su - gdqstatus

# Clone gdq collector repo
git clone https://github.com/bcongdon/gdq-collector
cd gdq-collector
mv gdq_collector/credentials_template.py gdq_collector/credentials.py

# Install dependencies (no longer necessary)
# pipenv --three
# pipenv install

# Setup AWS credentials
aws configure

# Setup EC2 CloudWatch metrics for memory / disk space
cd ~
curl http://aws-cloudwatch.s3.amazonaws.com/downloads/CloudWatchMonitoringScripts-1.2.1.zip -O
unzip CloudWatchMonitoringScripts-1.2.1.zip
rm CloudWatchMonitoringScripts-1.2.1.zip
cd aws-scripts-mon
mv awscreds.template ~/.awscreds.conf
cat <(crontab -l) <(echo "*/5 * * * * ~/aws-scripts-mon/mon-put-instance-data.pl --mem-used-incl-cache-buff --mem-util --disk-space-util --disk-space-avail --disk-space-used --disk-path=/ --from-cron --aws-credential-file=/home/ubuntu/.awscreds.conf") | crontab -

# Enter AWS credentials (can copy keys from ~/.aws/credentials)
vim ~/.awscreds.conf

# Install docker
sudo apt-get install apt-transport-https ca-certificates curl software-properties-common -y
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install docker-ce docker-compose -y

# Setup docker groups
sudo systemctl enable docker
sudo groupadd docker
sudo usermod -aG docker $USER

# log out and log back in
exit

# Build docker images
cd ~/gdq-collector
cp postgres-settings.env.template postgres-settings.env
# Generate and add postgres credentials
vim postgres-settings.env
# Add postgres settings to python credentials file
vim gdq_collector/credentials.py

# Update settings file to reflect new event
vim gdq_collector/settings.py

# Rebuild docker containers
docker-compose build
