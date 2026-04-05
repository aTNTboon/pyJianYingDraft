import re

def lrc_to_srt(lrc_path, srt_path):
    with open(lrc_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = []

    for line in lines:
        # 找到所有时间戳
        matches = re.findall(r'\[(\d+):(\d+(?:\.\d+)?)\]', line)
        if not matches:
            continue
        # 去掉所有时间戳，剩下就是文本
        text = re.sub(r'\[.*?\]', '', line).strip()
        if not text:
            continue
        # 每个时间戳都生成一条
        for m in matches:
            minute = int(m[0])
            second = float(m[1])
            start = minute * 60 + second
            entries.append((start, text))

    # 排序
    entries.sort(key=lambda x: x[0])

    # 写 SRT
    min_duration = 1.5
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (start, text) in enumerate(entries):
            if i + 1 < len(entries):
                end = entries[i + 1][0]
                if end - start < min_duration:
                    end = start + min_duration
            else:
                end = start + 3
            f.write(f"{i+1}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(f"{text}\n\n")

def format_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"