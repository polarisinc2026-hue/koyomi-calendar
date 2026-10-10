# 毎日安心カレンダー（koyomi-calendar）

「始めるのにいい日」「登山にいい日」「慎重にしたい日」がひと目でわかる、Googleカレンダー／iPhoneカレンダー用の無料カレンダーです。

登録ページ: https://polarisinc2026-hue.github.io/koyomi-calendar/

| ファイル | カレンダー名 | 内容 |
|---|---|---|
| `docs/koyomi-daily.ics` | 暦 | 毎日の六曜（詳細に十二直・旧暦・干支・吉日・凶日・判定） |
| `docs/kichijitsu.ics` | Chance!! | 新しいことを始めるのにいい日（天赦日・一粒万倍日など） |
| `docs/tozan.ics` | 登山日和⛰️ | 山に行くのにいい日と、毎月の休日のおすすめ |
| `docs/kyojitsu.ics` | 慎重に | 大事なことは避けたい日（不成就日・受死日・十死日） |

旧暦と二十四節気は天文計算（ephem）で求めています。「Chance!!」「登山日和」は伝統的な暦注をもとにした独自の判定です。

GitHub Actions（`.github/workflows/update.yml`）が毎月2日に「先月〜2年後の年末」を作り直します。
