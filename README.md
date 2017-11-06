# Mattermost CUGC Bot
## Developmet Setup
Can to use virtualenv or docker

### virtualenv
1. Install pip for python3
2. Install virtualenv `pip install virtualenv`
3. Create virtual environment `virtualenv ENV`
4. Activate virtual environment `source ENV/bin/activate`
5. Install requirements `pip install -r requirements.txt`
6. Start dev server `make run`

### Docker
1. Install Docker and Docker Compose
1. `docker-compose up`

## Mattermost Setup
1. Add slash command with URL `http://localhost:5000`