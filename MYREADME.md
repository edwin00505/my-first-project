## How to run:

```bash
cd ~
nvm use 20.18.2
source .venv/bin/activate
cd Downloads/edwin/app
yarn start-prod

# To start multiple instances to test live chat, set the `MULTI` environment variable to a unique value. You can start as many sessions as you want
yarn start-prod # Terminal A
MULTI=1 yarn start-prod # Terminal B
```
