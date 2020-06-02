# Simple Chat Program with Socket Programming

## 🗃️ 디렉토리 구조

```shell
📁SocketProgramming
├── Server.py
├── Client.py
└── library.py
```



## 💻 실행

### 환경

Linux (* Window 환경에서는 동작하지 않습니다.)

### 서버 오픈

```server
python3 server.py
```

### 클라이언트 실행

```
python3 client.py
```



## 👨‍💻 커맨드

### 서버

- `/ls`: 채팅방 목록 출력
- `/show clients`: 클라이언트 목록 출력
- `/exit`: 프로그램 종료
- `/kill [room_name]`: 특정 방 폭파



### 클라이언트

- `/ls`: 채팅방 목록 출력
- `/create [room_name][user_name]` :  `room_name` 이라는 이름의 방을 생성하여 `user_name` 으로 참여. user_name을 명시하지 않을 시 `Unknown` 으로 입장
- `/join [roon_name][user_name]`: `room_name`이라는 방에 `user_name`으로 참여
- `/whisper [member_name][message]`: 같은 방에 있는 대상 중 닉네임이 `user_name` 인 클라리언트에게 message를 귓속말로 전송
`/exit`: 채팅방에서 사용시 채팅방 나감. 방장일 경우 방 폭파. 대기실에서 사용시 클라이언트 종료



## 💡 IDEA

클라이언트에서 클라이언트의 상태를 관리하는 것은 보안적인 측면에서 매우 취약하다고 판단하였다. 따라서 클라이언트에서 실행하는 대부분의 명령어는 서버에서 처리가 되어 그 결과를 클라이언트에게 알리는 방식으로 동작한다.