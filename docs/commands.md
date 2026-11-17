# Commands

## Everyone

| Command | Description |
| --- | --- |
| `/start` | Start the bot in the chat (registers the chat and its schedule) |
| `/help` | Show the command reference |
| `/show_queue` | Show the queue of pending trophies as a table |
| `/delete_game` | Delete your most recently submitted trophy |
| `/history [@username]` | List all trophies of yourself or another user |
| `/top [dd.mm.yyyy]` | Trophy leaderboard, all-time or since the given date |
| `/games_info` | Wikipedia links for the games currently in the queue |

## Chat owner and bot admins

| Command | Description |
| --- | --- |
| `/settings` | Menu with buttons to set the interval, the day and hour of the next rotation, and the time zone |
| `/show_settings` | Show the next rotation date, the interval, the time zone and the default avatar |
| `/set_date DD/MM/YYYY HH:MM` | Set the next avatar rotation, in the chat's time zone |
| `/set_delta N` | Set the interval between rotations, 1–365 days; applies after the next rotation |
| `/set_timezone ZONE` | Set the chat's time zone: a city from the menu or an IANA name such as `Europe/Berlin` |

## Time zones

Each chat has its own time zone (Moscow by default). Dates in `/set_date`,
`/settings`, `/show_settings`, `/history` and `/top` are entered and shown in
it; the database stores them in UTC. Changing the zone does not move the next
rotation, and rotations keep their local time of day across DST changes.
Monthly survey results still follow UTC.

## Default avatar

Posting a photo captioned `@YourBotName *Default*` as a user with
*change group info* rights sets the chat's fallback avatar, used whenever the
queue runs dry.

## Tables

Tables (`/show_queue`, `/top`, `/history`, survey results) are sent as rich
messages with native table blocks (Bot API 10.1), so Telegram draws them and
the text stays selectable. See [`src.utility.rich_table`](reference/utility.md#src.utility.rich_table).
