import re

def lrc_to_srt(lrc_path, srt_path):
    with open(lrc_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    pattern = re.compile(r"\[(\d+):(\d+\.\d+)\](.*)")

    entries = []

    for line in lines:
        matches = pattern.findall(line)
        for m in matches:
            minute = int(m[0])
            second = float(m[1])
            text = m[2].strip()

            start = minute * 60 + second
            entries.append((start, text))

    # 排序
    entries.sort(key=lambda x: x[0])

    # 写 SRT
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (start, text) in enumerate(entries):
            end = entries[i + 1][0] if i + 1 < len(entries) else start + 3

            f.write(f"{i+1}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(f"{text}\n\n")


def format_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"