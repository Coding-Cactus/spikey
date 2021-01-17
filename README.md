# spikey
#### Discord moderation bot

- prefix: `+`
- invite: https://discordapp.com/oauth2/authorize?client_id=772385821180559390&scope=bot&permissions=0

## Commands

### Configuration
##### Only useable by server admins

- `+config_logs TextChannel` Choose to which channel the logs get sent
- `+config_mute Role` Choose which role to be added to a member when muted
- `+config_warn_mute time` Choose for how long a member will be muted after being warned
- `+config_strike_mute time` Choose for how long a member will be muted after being struck


### Infractions
##### Only useable by server moderators (except `+infractions`)

- `+warn Member <"reason">` Warn a member
- `+strike Member <"reason">` Strike a member
- `+infractions` view your infractions
  > Moderators can do `+infractions Member` to view a member's warns


### Repealing
#### Only useable by server moderators

- `+repeal_warn Member WarnID` Repeal one of a member's warnings
- `+repeal_strike Member StrikeID` Repeal one of a member's strikes


### Muting
#### Only useable by server moderators (except `+view_mutes`)

- `+mute Member <time>` adds the muted role (set by `config_mute`) to the for a specified time
  > If time is omitted, they will be muted indefinitely
- `+unmute Member` removes the muted role (set by `config_mute`) from a member
- `+view_mutes` View your current mutes across all the servers you and spikey are in
- `+view_server_mutes` View the current mutes in the server


### Members
#### Useable by any server member

- `+infractions` view your infractions
- `+view_mutes` View your current mutes across all the servers you and spikey are in
