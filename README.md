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


## My Workflow (you need admin permissions)
### setting up a new semester
#### creating the channel infrastructure
(I recommend at least two discord instances for this process. Best is three. Two with your main account, one with a secondary account that has normal permissions.)
* Clone the currents semester category channel using `/cp source dest_name` to get a category with the correct case permissions
* Ensure in the server settings that the roles are correctly sorted by semester, fix potential issues
* Use `/rename_roles` to rename all roles. Example: `/rename_roles lower_role: @----WS22/23---- upper_role: @----SoSe23---- to_add: (ss23)` 
* Create a new placeholder-role (above the old semester (arbitrary, but I group them like that))
* Create / move a prototype-channel and role that represents a module channel with its related role.
  * Configure the channels general permissions and the module-roles specific overwrites within this channel
* Use `/clone_category_with_new_roles` to fill the new semesters category with life
  * `source_category`: use the old semester as source
  * `old_module_selection_channel`: pass its module selection channel (this is needed because the channel doesn't need a special role)
  * `prototype_channel`:  give a prototype channel that holds the default permissions for a module channel (and configure the prototype-roles permissions)
  * `prototype_role`: give prototype role that represents the (permission) overwrites a module-role shall have inside the related channel
  * `destination_category`: give destination category (the one you created earlier)
  * `new_roles_below`: give the manually created placeholder-role
  * press enter, pray and monitor the bots logs, the category as well as the roles overview closely (if this goes wrong you've got a lot of cleanup to do!)
    * If you f\*ck it up - there is (now whilst writing this) a new revert context-command `revert_channel_creation` that can revert what you've done by utilizing the result message.
* Check that all roles were created correctly (even tough creating a role shouldn't be hard, discord always messes up the positioning!)
* Check that all permissions are right

#### create the selection message
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


### documentation
In order to render this documentation, just call `doxygen`
