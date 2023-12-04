# Channel Mover
Utilities to move, rename and create a lot of channels at once, following various schemes and more useful stuff.  
The code is documented but usage and required schemes aren't.  
It's just a collection of \*very specific\* commands that make maintaining our server a lot easier and are only needed twice a year.  
The structuring of functionality into dedicated modules is also optional at this point.  
You can find all of the actual functionality in `src/discord_bot/cogs/misc.py` (:

## Setup (if you really feel like this bot is any good for you)

###### Setup a [venv](https://docs.python.org/3/library/venv.html) (optional, but recommend)
`python3 -m venv venv`   
`source venv/bin/activate` 


##### Using pip to install the bot as editable package:  
` python3 -m pip install -e .`  
`export TOKEN="your-key"`  
`discord-bot`  
##### Or using the launch script:  
`pip install -r requirements.txt`  
`export TOKEN="your-key"`   
`python3 ~/git/discord-bot/launcher.py`  

### Intents
The bot uses all intents by default, those are required for such simple things like 'display member-count at startup'.  
You need to enable those intents in the [discord developers portal](https://discord.com/developers/applications) 
under `*YourApplication*/Bot/Privileged Gateway Intents`.   
It's possible reconfigure the requested intents in `main.py` if you don't need them.  
But I'd suggest using them all for the beginning, especially if you're relatively new to discord.py.  
This will only be an issue if your bot reaches more than 100 servers, then you've got to apply for those intents. 

#### Optional env variables
| parameter |  description |
| ------ |  ------ |
| `PREFIX="b!"`  | Command prefix |
| `OWNER_NAME="unknwon"` | Name of the bot owner |
| `OWNER_ID="100000000000000000"` | ID of the bot owner |
| `ACTIVITY_NAME=f"{PREFIX}help"`| Activity bot plays |  

The shown values are the default values that will be loaded if nothing else is specified.  
Expressions like `{PREFIX}` will be replaced by during loading the variable and can be used in specified env variables.

Set those variables using env-variables (suggested):  
`export PREFIX="b!"`  
Or use a json-file expected at: `./data/config.json` like:  
```json
{
  "TOKEN": "[your-token]",
  "PREFIX": "b!"
}
```

_If a variable is set using env and json **the environment-variable replaces the json**!_

### documentation
In order to render this documentation, just call `doxygen`
