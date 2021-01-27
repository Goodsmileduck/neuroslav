# neuroslav



# Start mongo


```
docker-compose up -d mongo
```
db saved docker volume `mongo-volume`
don't delete it if don't want to lost data


# Start app

```
docker-compose up -d neuroslav
```

# Start ngrok

```
docker-compose up -d ngrok
```

# Start all at same time

```
docker-compose up -d
```

# Get ngrok link

```
docker logs ngrok
+ exec ngrok http -log stdout neuroslav:5000
t=2021-01-27T09:29:37+0000 lvl=info msg="no configuration paths supplied"
t=2021-01-27T09:29:37+0000 lvl=info msg="ignoring default config path, could not stat it" path=/home/ngrok/.ngrok2/ngrok.yml err="stat /home/ngrok/.ngrok2/ngrok.yml: no such file or directory"
t=2021-01-27T09:29:37+0000 lvl=info msg="starting web service" obj=web addr=127.0.0.1:4040
t=2021-01-27T09:29:38+0000 lvl=info msg="tunnel session started" obj=tunnels.session
t=2021-01-27T09:29:38+0000 lvl=info msg="client session established" obj=csess id=97912ac1c297
t=2021-01-27T09:29:39+0000 lvl=info msg="started tunnel" obj=tunnels name="command_line (http)" addr=http://neuroslav:5000 url=http://7dc49b5fba38.ngrok.io
t=2021-01-27T09:29:39+0000 lvl=info msg="started tunnel" obj=tunnels name=command_line addr=http://neuroslav:5000 url=https://7dc49b5fba38.ngrok.io
```


`http://7dc49b5fba38.ngrok.io` and  `https://7dc49b5fba38.ngrok.io` will be links for tunnel


# Shutdown compose

```
docker-compose down
```