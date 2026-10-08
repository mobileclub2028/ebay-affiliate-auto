# RefurbPrice US — eBay 자동화 시스템

무료 스택: Python + GitHub Actions + GitHub Pages + Telegram.
니치: 미국 중고 테크 3종 (ThinkPad X1 / iPhone 13 / XPS 13).

## 네가 할 일 (최소, 15분)
1. `developers.ebay.com` → App ID + Cert ID 발급
2. EPN 메일의 `campid` 복사
3. Telegram `@BotFather` → 봇 생성 → 토큰 + `@userinfobot`으로 chat_id 확보
4. GitHub repo 만들고 이 폴더 push → Settings → Secrets에 5개 등록:
   `EBAY_APP_ID, EBAY_CERT_ID, EPN_CAMPID, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID`
5. Settings → Pages → Source: `docs/` → 사이트 URL을 `config.yaml site_url`에 입력

## 로컬 실행
```
pip install -r requirements.txt
python src/fetch_ebay.py
python src/build_pages.py
# docs/index.html 열어서 확인
```

키 없이도 mock 데이터로 빌드됨. 키 넣으면 live 모드로 전환.
