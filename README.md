# おかぴー暦（koyomi-calendar）

「はじめ日」「山日和」「あちゃー日」がひと目でわかる、Googleカレンダー／iPhoneカレンダー用の無料の暦です。

登録ページ: https://polarisinc2026-hue.github.io/koyomi-calendar/

| ファイル | カレンダー名 | 内容 |
|---|---|---|
| `docs/koyomi-daily.ics` | おかぴー暦 | 毎日の六曜と 🌱はじめ日 ⛰山日和 🙈あちゃー日 のしるし（詳細に十二直・旧暦・干支） |
| `docs/kichijitsu.ics` | おかぴー はじめ日 | 新しいことを始めるのにいい日（天赦日・一粒万倍日など） |
| `docs/tozan.ics` | おかぴー 山日和 | 山に行くのにいい日と、毎月の休日のおすすめ |
| `docs/kyojitsu.ics` | おかぴー あちゃー日 | 気をつける日（不成就日・受死日・十死日） |

旧暦と二十四節気は天文計算（ephem）で求めています。🌱⛰の判定は伝統的な暦注をもとにした「おかぴーオリジナル判定」です。

GitHub Actions（`.github/workflows/update.yml`）が毎月2日に「先月〜2年後の年末」を作り直します。
