# reddit2tg
Telegram bot that sends Tumblr posts (from tags and blogs).

# How it works
The bot schedules a task (with a [cron expression](https://www.wikiwand.com/en/Cron#/CRON_expression)) to send posts to a Telegram channel.

# Configuration
- Make copy `config.json.example` as `config.json`.
- Create a bot with [BotFather](https://t.me/BotFather)
- Get OAuth Consumer Key from [Tumblr](https://www.tumblr.com/oauth/apps)
- Create a public Telegram channel or private one and [get the private id](https://stackoverflow.com/a/39943226)


Then fill the configuration file:
## Configuration file
config.json escructure:
```jsx
{
    "telegram": {
        "bot_token": ""
    },
    "tumblr": {
        "api_token": ""
    },
    "config": {
        "channels": {
            "channel_id": {
                "cron": "",
                "tumblr_sources": [
                    {   
                        "type": "",
                        "name": ""
                    }
                ]
            }
        },
        "admin" : "id"
    }
}
```

## Parameters for ``telegram`` and ``tumblr``
| name  | type  | required  | description 
|---|---|---|---|
| bot_token  | string  | true |  Token from a [BotFather](https://t.me/BotFather) bot. |   |
| api_token  | string  | true  |  OAuth Consumer Key from [Tumblr](https://www.tumblr.com/oauth/apps). |   |

## Parameters for ``channels``
Object to store the Telegram channels that you want to send posts to. Every channel is idenfied by the ```channel_id``` key.

| name  | type  | required  | description  |  
|---|---|---|---|
| channel_id  |  string | true  | Unique identifier for the target chat or username of the target channel (can be public channel (@channelusername) or a private one([get id of private channel](https://stackoverflow.com/a/39943226)).  |   |

### Parameters for ``cron``
| name  | type  | required  | description  |  
|---|---|---|---|
| channel_id  | string  | true  | [Cron expression](https://crontab.guru/) that tells the program when to send a new post.  |   |

### Parameters for ``tumblr_sources``
An array that of the sources that you want the posts from. Add multiple objects with the ``type`` and ``name`` keys to add new sources.

| name  | type  | required  | description  |  
|---|---|---|---|
| type  | string  | true  | Accepts the value of ``blog`` or ``tag`` to send posts from a blog or posts from a tag. |
| name  | string | true  |  Name of the blog or the tag.  |

## Parameters for ``admin``
| name  | type  | required  | description  |  
|---|---|---|---|
| admin  |  string | false  | Your Telegram username tag or [id](https://t.me/userinfobot)


## Configuration file example
```jsx
{
    "telegram": {
        "bot_token": ""
    },
    "tumblr": {
        "api_token": ""
    },
    "config": {
        "channels": {
            "channel123": {
                "cron": "* * * *", //to send a post every minut
                "tumblr_sources": [ // will send posts that have tag dog or post from monicore.online
                    {   
                        "type": "tag",
                        "name": "dog"
                    }
                    {   
                        "type": "blog",
                        "name": "monicore.online"
                    }
                ]
            }
        },
        "admin" : "username123"
    }
}
```
# Deployment
## With Docker
- ``docker-compose up -d`` to create and start the container
- ???? profit
## Without Docker
- Install the depencies with ``pip3 install -r requirements.txt``
- ``python app.py`` to execute the script
