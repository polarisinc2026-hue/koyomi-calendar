# 暦カレンダー（koyomi-calendar）

日本の暦注をGoogleカレンダーで購読するためのicsフィードです。旧暦と二十四節気を天文計算（ephem）で求めて生成しています。

| ファイル | 内容 |
|---|---|
| `docs/koyomi-daily.ics` | 毎日：六曜・十二直・旧暦・干支・登山/新しいことの判定（◎○△×） |
| `docs/kichijitsu.ics` | 吉日：天赦日・一粒万倍日・寅の日・巳の日・己巳の日・甲子の日 |
| `docs/kyojitsu.ics` | 凶日：不成就日・受死日・十死日・三隣亡 |
| `docs/tozan.ics` | 登山日和：登山◎の日と、各月の土日祝ベスト |

購読URL: `https://polarisinc2026-hue.github.io/koyomi-calendar/<ファイル名>`

GitHub Actions（`.github/workflows/update.yml`）が毎月2日に「先月〜2年後の年末」を作り直します。

暦注は伝統的な目安です。登山は天気予報を最優先にしてください。
