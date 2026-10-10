# -*- coding: utf-8 -*-
"""
毎日安心カレンダー：日本の暦注カレンダー生成スクリプト（Googleカレンダー取り込み用 .ics）
- 旧暦（六曜・不成就日）と二十四節気（節月：一粒万倍日・十二直など）を天文計算で求める
- 使い方: python3 koyomi.py [開始日] [終了日] [出力先]
  （引数なしなら「先月1日〜2年後の年末」を作る。GitHub Actionsが毎月これを実行）
"""
import sys, math, datetime as dt
import ephem, jpholiday

JST = dt.timedelta(hours=9)
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
ROKUYO = ["大安", "赤口", "先勝", "友引", "先負", "仏滅"]

# ---------- 天文計算 ----------
def to_jst_date(edate):
    return (ephem.Date(edate).datetime() + JST).date()

def sun_lon(d):
    s = ephem.Sun(d)
    return math.degrees(ephem.Ecliptic(ephem.Equatorial(s.ra, s.dec, epoch=d), epoch=d).lon)

def solar_term_times(start, end):
    """(JST日付, 黄経) のリスト。15度ごとの二十四節気"""
    res = []
    d = ephem.Date(start - dt.timedelta(days=40))
    stop = ephem.Date(end + dt.timedelta(days=40))
    step = 0.5
    prev = sun_lon(d)
    while d < stop:
        n = ephem.Date(d + step)
        cur = sun_lon(n)
        a, b = math.floor(prev / 15), math.floor(cur / 15)
        if a != b:
            target = (b * 15) % 360
            lo, hi = float(d), float(n)
            for _ in range(50):
                mid = (lo + hi) / 2
                diff = (sun_lon(mid) - target + 180) % 360 - 180
                if diff < 0: lo = mid
                else: hi = mid
            res.append((to_jst_date(hi), target))
        d, prev = n, cur
    return res

def new_moons(start, end):
    res = []
    d = ephem.Date(start - dt.timedelta(days=400))
    stop = ephem.Date(end + dt.timedelta(days=60))
    while d < stop:
        d = ephem.next_new_moon(d)
        res.append(to_jst_date(d))
        d = ephem.Date(d + 1)
    return res

SEKKI_NAME = {315:"立春",330:"雨水",345:"啓蟄",0:"春分",15:"清明",30:"穀雨",45:"立夏",60:"小満",
              75:"芒種",90:"夏至",105:"小暑",120:"大暑",135:"立秋",150:"処暑",165:"白露",180:"秋分",
              195:"寒露",210:"霜降",225:"立冬",240:"小雪",255:"大雪",270:"冬至",285:"小寒",300:"大寒"}

def build_lunar(start, end, terms, moons):
    """日付 -> (旧暦月, 閏フラグ, 旧暦日)"""
    chuki = {d: lon for d, lon in terms if lon % 30 == 0}   # 中気
    lunar = {}
    prev_month = None
    for i in range(len(moons) - 1):
        a, b = moons[i], moons[i + 1]
        m = None
        day = a
        while day < b:
            if day in chuki:
                m = int(((chuki[day] // 30) + 2) % 12) or 12   # 春分(0)=2月, 冬至(270)=11月
                break
            day += dt.timedelta(days=1)
        leap = m is None
        if leap:
            m = prev_month if prev_month else 0
        prev_month = m
        day = a
        while day < b:
            lunar[day] = (m, leap, (day - a).days + 1)
            day += dt.timedelta(days=1)
    return lunar

def sekki_month_branch(date, setsu_list):
    """節入り日で切り替わる節月の地支インデックス"""
    lon = None
    for d, l in setsu_list:
        if d <= date: lon = l
        else: break
    return int((2 + ((lon - 315) % 360) // 30) % 12)

# ---------- 暦注の表 ----------
def kanshi_index(date):
    jdn = date.toordinal() + 1721425
    return (jdn + 49) % 60

ICHIRYU = {2:"丑午",3:"酉寅",4:"子卯",5:"卯辰",6:"巳午",7:"酉午",8:"子未",9:"卯申",10:"午酉",11:"酉戌",0:"亥子",1:"卯子"}
FUJOJU = {1:[3,11,19,27],7:[3,11,19,27],2:[2,10,18,26],8:[2,10,18,26],3:[1,9,17,25],9:[1,9,17,25],
          4:[4,12,20,28],10:[4,12,20,28],5:[5,13,21,29],11:[5,13,21,29],6:[6,14,22,30],12:[6,14,22,30]}
DAIMYO = {i - 1 for i in [6,7,8,9,10,14,16,19,21,24,29,32,39,41,42,43,44,46,47,48,53,55,56,57,58]}
TENON = set(range(0,5)) | set(range(15,20)) | set(range(45,50))
JUSHI = {2:"戌",3:"辰",4:"亥",5:"巳",6:"子",7:"午",8:"丑",9:"未",10:"寅",11:"申",0:"卯",1:"酉"}
JISSHI = {2:"酉",6:"酉",10:"酉",3:"巳",7:"巳",11:"巳",4:"丑",8:"丑",0:"丑",5:"子",9:"子",1:"子"}
SANRIN = {2:"亥",5:"亥",8:"亥",11:"亥",3:"寅",6:"寅",9:"寅",0:"寅",4:"午",7:"午",10:"午",1:"午"}
TENSHA = {"春":"戊寅","夏":"甲午","秋":"戊申","冬":"甲子"}
BOSO = {"春":"亥子","夏":"寅卯","秋":"辰戌丑未","冬":"申酉"}

JUNICHOKU = ["建","除","満","平","定","執","破","危","成","納","開","閉"]
CHOKU_INFO = {
 "建":("物事を建て始める日","開店・新規事業・祭り・旅行","土を掘る工事・蔵開き"),
 "除":("障りを取り除く日","掃除・治療の開始・お祓い","結婚・土を掘る工事"),
 "満":("すべてが満ちる日","移転・結婚・新規事業・建築","土を掘る工事・薬を飲み始める"),
 "平":("物事が平らに収まる日","旅行・地固め・結婚・話し合い","穴掘り・種まき"),
 "定":("善悪が定まる日","開店・契約・売買・移転・結婚","旅行・訴訟"),
 "執":("物事を執り行う日","祭り・結婚・種まき・建築","大きなお金の出し入れ"),
 "破":("物事を破る日","交渉ごとの決着・解体・漁","お祝い事・契約・旅行"),
 "危":("危うい日、万事控えめに","控えめな行動・準備","登山・船出・旅行"),
 "成":("物事が成就する日","新規事業・開店・建築・結婚","訴訟・談判"),
 "納":("物事を納める日","収穫・買い物・入学・結婚","葬儀・お見合い"),
 "開":("道が開ける日","開業・移転・結婚・建築","葬儀・不浄ごと"),
 "閉":("閉じてしまう日","お金を貯める・墓・トイレ工事","開業・結婚・旅行"),
}
ROKUYO_INFO = {
 "大安":"終日吉。何をしても良い日",
 "赤口":"正午前後のみ吉、それ以外は凶。火・刃物に注意",
 "先勝":"午前は吉、午後は凶。急ぐことは吉",
 "友引":"朝夕は吉、昼は凶。勝負なし（葬儀は避ける習わし）",
 "先負":"午前は凶、午後は吉。急がず控えめに",
 "仏滅":"終日凶。新しいことは控えめに",
}
KICHI_INFO = {
 "天赦日":"年に数回の最上の吉日。何を始めても良い",
 "一粒万倍日":"小さな一歩が万倍に。始める・お金を使うのに吉（借金は避ける）",
 "天恩日":"天の恩を受ける日。お祝い事に吉",
 "大明日":"太陽が隅々まで照らす日。移動・旅行・建築に吉",
 "母倉日":"天が母のように慈しむ日。結婚・建築に吉",
 "寅の日":"千里行って千里帰る。旅立ち・お金に吉（結婚は×）",
 "巳の日":"弁財天の日。金運・芸事に吉",
 "己巳の日":"60日に1度の巳の日。金運が特に強い",
 "甲子の日":"60日周期の始まり。新しく始めるのに吉",
 "天一天上":"方角の神が天に昇る16日間。どの方角へ出かけても障りなし",
}
KYO_INFO = {
 "不成就日":"何事も成就しない日。始めることは避ける",
 "受死日":"暦の上でいちばん注意な日。大事なことは別の日に",
 "十死日":"何かとうまくいきにくい日。始めること・遠出は控えめに",
 "三隣亡":"建築の大凶日（棟上げ・工事は避ける）",
}

def day_info(date, lunar, setsu, terms, doyo_set):
    k = kanshi_index(date)
    stem, br = k % 10, k % 12
    kanshi = STEMS[stem] + BRANCHES[br]
    lm, leap, ld = lunar[date]
    rokuyo = ROKUYO[(lm + ld) % 6]
    mb = sekki_month_branch(date, setsu)
    choku = JUNICHOKU[(br - mb) % 12]
    season = {2:"春",3:"春",4:"春",5:"夏",6:"夏",7:"夏",8:"秋",9:"秋",10:"秋",11:"冬",0:"冬",1:"冬"}[mb]
    in_doyo = date in doyo_set

    kichi, kyo = [], []
    if kanshi == TENSHA[season]: kichi.append("天赦日")
    if BRANCHES[br] in ICHIRYU[mb]: kichi.append("一粒万倍日")
    if k in TENON: kichi.append("天恩日")
    if k in DAIMYO: kichi.append("大明日")
    boso = "巳午" if in_doyo else BOSO[season]
    if BRANCHES[br] in boso: kichi.append("母倉日")
    if br == 2: kichi.append("寅の日")
    if kanshi == "己巳": kichi.append("己巳の日")
    elif br == 5: kichi.append("巳の日")
    if k == 0: kichi.append("甲子の日")
    if 29 <= k <= 44: kichi.append("天一天上")

    if ld in FUJOJU[lm]: kyo.append("不成就日")
    if BRANCHES[br] == JUSHI[mb]: kyo.append("受死日")
    if BRANCHES[br] == JISSHI[mb]: kyo.append("十死日")
    if BRANCHES[br] == SANRIN[mb]: kyo.append("三隣亡")

    sekki = next((SEKKI_NAME[l] for d, l in terms if d == date and l in SEKKI_NAME), None)
    return dict(date=date, kanshi=kanshi, kidx=k, lunar=(lm, leap, ld), rokuyo=rokuyo,
                choku=choku, kichi=kichi, kyo=kyo, sekki=sekki, doyo=in_doyo,
                holiday=jpholiday.is_holiday_name(date))

# ---------- スコア ----------
def mountain_score(info):
    s, why = 0, []
    def add(p, r):
        nonlocal s; s += p; why.append(f"{r}{'+' if p>0 else ''}{p}")
    if "寅の日" in info["kichi"]: add(2, "寅の日(行って無事に帰る)")
    if "天赦日" in info["kichi"]: add(1, "天赦日")
    if "大明日" in info["kichi"]: add(1, "大明日(旅行吉)")
    if "天一天上" in info["kichi"]: add(1, "天一天上(どの方角もOK)")
    c = info["choku"]
    if c in ("建", "平", "開"): add(1, f"{c}(出かけるのに吉)")
    if c == "危": add(-3, "危(登山は凶)")
    if c in ("破", "定", "閉"): add(-1, f"{c}(旅行に不向き)")
    r = info["rokuyo"]
    if r == "大安": add(1, "大安")
    if r == "先勝": add(1, "先勝(午前吉＝早朝出発と相性よし)")
    if r in ("仏滅", "赤口"): add(-1, r)
    if "受死日" in info["kyo"]: add(-2, "受死日")
    if "十死日" in info["kyo"]: add(-2, "十死日")
    if "不成就日" in info["kyo"]: add(-2, "不成就日")
    return s, why

def start_score(info):
    s, why = 0, []
    def add(p, r):
        nonlocal s; s += p; why.append(f"{r}{'+' if p>0 else ''}{p}")
    k = info["kichi"]
    if "天赦日" in k: add(3, "天赦日")
    if "一粒万倍日" in k: add(2, "一粒万倍日")
    if "天恩日" in k: add(1, "天恩日")
    if "大明日" in k: add(1, "大明日")
    if "甲子の日" in k: add(1, "甲子の日")
    c = info["choku"]
    if c in ("建", "満", "成", "開"): add(1, f"{c}(始めるのに吉)")
    if c in ("破", "危", "閉"): add(-1, f"{c}(始めるのに不向き)")
    r = info["rokuyo"]
    if r == "大安": add(1, "大安")
    if r in ("仏滅", "赤口"): add(-1, r)
    if "不成就日" in info["kyo"]: add(-3, "不成就日")
    if "受死日" in info["kyo"]: add(-2, "受死日")
    if "十死日" in info["kyo"]: add(-2, "十死日")
    return s, why

def grade(s):
    return "◎" if s >= 3 else "○" if s >= 1 else "△" if s >= -1 else "×"

# ---------- ICS ----------
def esc(t):
    return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def fold(line):
    out, cur = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        if len(cur) + len(b) > 73:
            out.append(cur.decode("utf-8")); cur = b" " + b
        else:
            cur += b
    out.append(cur.decode("utf-8"))
    return "\r\n".join(out)

def ics(name, desc, events):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MainichiAnshin//Koyomi//JA", "CALSCALE:GREGORIAN",
             "METHOD:PUBLISH", f"X-WR-CALNAME:{esc(name)}", f"X-WR-CALDESC:{esc(desc)}", "X-WR-TIMEZONE:Asia/Tokyo"]
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for uid, date, title, body in events:
        lines += ["BEGIN:VEVENT", f"UID:{uid}@koyomi.okapi", f"DTSTAMP:{stamp}",
                  f"DTSTART;VALUE=DATE:{date:%Y%m%d}", f"DTEND;VALUE=DATE:{date + dt.timedelta(days=1):%Y%m%d}",
                  f"SUMMARY:{esc(title)}", f"DESCRIPTION:{esc(body)}", "TRANSP:TRANSPARENT", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in lines) + "\r\n"

KICHI_MARK = {"天赦日":"💎","一粒万倍日":"🌾","天恩日":"🌈","大明日":"☀️","母倉日":"🤱","寅の日":"🐯",
              "巳の日":"🐍","己巳の日":"🐍✨","甲子の日":"🔰","天一天上":"🧭"}
KYO_MARK = {"不成就日":"🙈","受死日":"⚠️","十死日":"🤦","三隣亡":"🚧"}
ACHA = ["不成就日", "受死日", "十死日"]   # あちゃー日に出す凶日（三隣亡は建築だけの話なので毎日の詳細のみ）
MAIN_KICHI = ["天赦日","一粒万倍日","寅の日","己巳の日","巳の日","甲子の日"]

def generate(start, end, outdir="."):
    terms = solar_term_times(start, end)
    setsu = [(d, l) for d, l in terms if l % 30 == 15]
    moons = new_moons(start, end)
    lunar = build_lunar(start, end, terms, moons)
    # 土用期間：立春/立夏/立秋/立冬の前日までの、太陽黄経 297/27/117/207 度以降
    doyo_set = set()
    for d, l in setsu:
        if l in (315, 45, 135, 225):
            # 土用入り = 黄経が (立の黄経 - 18度) を越えた日
            target = (l - 18) % 360
            day = d - dt.timedelta(days=25)
            while day < d:
                end_of_day_utc = dt.datetime.combine(day, dt.time(15))  # = JST 当日24時
                lon = sun_lon(ephem.Date(end_of_day_utc))
                if (lon - target) % 360 < 30: doyo_set.add(day)
                day += dt.timedelta(days=1)

    infos = []
    d = start
    while d <= end:
        infos.append(day_info(d, lunar, setsu, terms, doyo_set)); d += dt.timedelta(days=1)

    daily, good, bad, mount = [], [], [], []
    for inf in infos:
        d = inf["date"]
        ms, mwhy = mountain_score(inf); ss, swhy = start_score(inf)
        inf["m"], inf["s"] = grade(ms), grade(ss)
        inf["ms"], inf["ss"] = ms, ss
        lm, leap, ld = inf["lunar"]
        cmean, cgood, cbad = CHOKU_INFO[inf["choku"]]
        acha = [x for x in ACHA if x in inf["kyo"]]
        title = inf["rokuyo"] + (f"　{inf['sekki']}" if inf["sekki"] else "")
        body = [
            f"旧暦 {'閏' if leap else ''}{lm}月{ld}日／{inf['kanshi']}の日" + ("／土用" if inf["doyo"] else ""),
            "",
            f"■六曜：{inf['rokuyo']} … {ROKUYO_INFO[inf['rokuyo']]}",
            f"■十二直：{inf['choku']} … {cmean}",
            f"　向いている：{cgood}",
            f"　向いていない：{cbad}",
        ]
        if inf["kichi"]:
            body += ["", "■吉日"] + [f"　{x} … {KICHI_INFO[x]}" for x in inf["kichi"]]
        if inf["kyo"]:
            body += ["", "■凶日"] + [f"　{x} … {KYO_INFO[x]}" for x in inf["kyo"]]
        body += ["", f"■登山 {inf['m']}（{ms:+d}）: " + ("、".join(mwhy) or "特記なし"),
                 f"■新しいこと {inf['s']}（{ss:+d}）: " + ("、".join(swhy) or "特記なし"),
                 "", "◎=おすすめ ○=良い △=普通 ×=避けたい（毎日安心カレンダー独自の判定）"]
        body = "\n".join(body)
        daily.append((f"d{d:%Y%m%d}", d, title, body))

        big = [x for x in ("天赦日", "一粒万倍日") if x in inf["kichi"]]
        if inf["s"] == "◎" or (big and not acha):
            why = [x for x in MAIN_KICHI if x in inf["kichi"]][:2]
            if inf["rokuyo"] == "大安": why.append("大安")
            head = "Chance!!👑最強開運日" if len(big) == 2 else "Chance!!"
            good.append((f"g{d:%Y%m%d}", d, head + (f"（{'・'.join(why)}）" if why else ""), body))
        if acha:
            bad.append((f"b{d:%Y%m%d}", d, "慎重に", "慎重にしたい理由：" + "・".join(acha) + "\n\n" + body))

    # 登山カレンダー：◎の日すべて＋各月の「週末・祝日ベスト」
    by_month = {}
    for inf in infos:
        by_month.setdefault((inf["date"].year, inf["date"].month), []).append(inf)
    for ym, lst in by_month.items():
        for inf in lst:
            if inf["m"] == "◎":
                d = inf["date"]
                off = d.weekday() >= 5 or inf["holiday"]
                mount.append((f"m{d:%Y%m%d}", d, f"登山日和⛰️{'（休日）' if off else ''}", daily[infos.index(inf)][3]))
        offs = [x for x in lst if x["date"].weekday() >= 5 or x["holiday"]]
        if offs:
            best = max(offs, key=lambda x: (x["ms"], x["ss"]))
            if best["m"] != "◎" and best["ms"] >= 0:
                d = best["date"]
                mount.append((f"m{d:%Y%m%d}", d, f"今月の休日の登山日和⛰️（{best['m']}）", daily[infos.index(best)][3]))
    mount.sort(key=lambda e: e[1])

    files = {
        "koyomi-daily.ics": ("暦", "毎日安心カレンダー：毎日の六曜。タップすると向いていること・いないことがわかります", daily),
        "kichijitsu.ics": ("Chance!!", "毎日安心カレンダー：新しいことを始めるのにいい日（天赦日・一粒万倍日など）", good),
        "kyojitsu.ics": ("慎重に", "毎日安心カレンダー：大事なことは避けたい日（不成就日・受死日・十死日）", bad),
        "tozan.ics": ("登山日和⛰️", "毎日安心カレンダー：山に行くのにいい日と、毎月の休日のおすすめ", mount),
    }
    for fn, (name, desc, ev) in files.items():
        with open(f"{outdir}/{fn}", "w", encoding="utf-8", newline="") as f:
            f.write(ics(name, desc, ev))
    return infos, files

if __name__ == "__main__":
    # 引数なし: 先月1日から2年後の年末まで（毎月の自動更新用）
    today = dt.date.today()
    first = today.replace(day=1)
    default_s = (first - dt.timedelta(days=1)).replace(day=1)
    default_e = dt.date(today.year + 2, 12, 31)
    s = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "-" else default_s
    e = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "-" else default_e
    out = sys.argv[3] if len(sys.argv) > 3 else "."
    infos, files = generate(s, e, out)
    for fn, (_, _, ev) in files.items():
        print(fn, len(ev), "件")
