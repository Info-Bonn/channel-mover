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

## My new Workflow (you need admin permissions)

There is a function called `misc.merge()` that does essentially all parts that are todo but with more edge case handling

### Clearing the roles
*Make a role backup using `/role_backup`
* Specify a list of roles you wanna clear
  * TODO: auto generate this list by passing a category and identifying the roles using `get_channel_role()`
* Ensure that the `RoleName (old)` role exists (or let the function create that if needed - `merge()` does that)
* Move all members from the current role to the `old`-role (`merge()` can do that)
* Manually Check that all targeted roles are indeed empty

### Tutor Handling + "You're in the old semester"-message
* Note: the tutors pool is (only) cleared on bot restart. keep that in mind.
* If tutors were collected: use `add_tutor_annotations` (context menu command) to add them to the pool (you can add multiple messages)
* Remove all tutors that did not consent from the pool using `/rm_tutor` (TODO: this malfunctioned last time)
  * Do a manual sanity check if nobody was mentioned that didn't want to be.
* Use `/finish_channels` on the category you wanna close. Provide the old semester tag to it.
  * The bot will send the closure message and attach the tutors if any.

* Remember to remove all tutors that are no longer tutors. I tried automatic it based on a message reaction, but it sucked.


##### Documenting the Tutors
* create messages that holds all modules and tutors in the following format:
```
#module-channel-1
@module-tutor-1
@tutor-2

#module-channel-n
@module-tutor-n
@module-tutor-n+1
```
* use the context action `add_tutor_annotations` on that message
  * the bot will parse the message and add them to its - in memory - pool


### Reaction Roles

#### Cleaning Reaction Roles (this takes a while)
* Use the context menu command `clear_reactions` for that.
  * The bot will keep the reactions of the reaction role bot. (the id is hardcoded in the command rn...)

#### Ensuring the modules are up to date
See section `create the selection message` 

#### create the selection message
(You can recycle the old channel and message and edit it in place...)
* Create the new choose-module message (make it visible only for admins)
* Create the selection channel
* Create a webhook (or redirect an existing one)
* Go to https://discohook.org (note: the send button is currently broken in firefox but it works in chrome)
* Recreate the old message (I recommend using their bot's context function to get the old content back)
* Check that the general information texts are correct
* Ensure that all modules are actually offered
* Add new modules
  * Make sure that there are not more than 20 modules per message or you'll get problems when adding the reactions due to discords arbitrary limitations
* Check that all the standard / permanent roles are added
* Send the messages
* Add reaction roles with bot of your choice (we use our [own](https://github.com/Eschryn/r0le) in house bot with the prefix `~rr`)
* Test the system with an alt account without admin permissions
* Create a thread below the messages asking for any addition
* Open the channel to everyone, make sure to not allow new reactions and messages

### Hiding the old semester
* You can use `/toggle_role_for_category` to add the `Archivbesuch`-Rolle to the category (and remove it later)
