## LeaffealBot (RemindMoKoBot)
my personal (abandoned) discord bot reminder and task organizer/helper  
made in 2 weeks  
developed on mobile using [Acode Editor](https://acode.app/) and [Termux](https://termux.dev/)  

---

## features
- create task (or quest) and display it on a specific channel
- edit task
- display pending tasks in a specific channel with refresh button (see deadlines with days remaining)
- calendar command
- log template command (helped me a lot)
- server invite creation command with specific expiration and user limit
- export database as json file
- view redis database (edit and delete)

---

### what you need:
- [Discord bot](https://discord.com/developers/applications)
- [Redis Database](https://redis.com/try-free/)

### setup:

```
git clone https://github.com/bnjmzzn/leaffealbot.git
cd leaffealbot
pip install -r requirements.txt
```

### `storage/.env` example:

```
DISCORD_TOKEN = ajshfhcncjs.mxnxjn.sjsncjxnsjdhshaksnxn
REDIS_HOST = abcdefghijklmnopqrstuvwxyz.cloud.redislabs.com
REDIS_PORT = 9999
REDIS_PASSWORD = abcde1234
```

### run:

```
python main.py
```

### demo video:

https://github.com/bZnjZmZn/leaffealbot/assets/148628055/d3025bee-5777-4680-9eac-82c6c45bff7b