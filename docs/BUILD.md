# 빌드 방법

번역 대본·원문은 저장소에 없으므로, 아래는 자신이 가진 원본과 번역 파일로 다시 빌드하는 절차입니다.

## 준비물
- 원본 ISO `Gachitora! Abarenbou Kyoushi in High School (Japan).iso` (MD5 `813aa8aeb9cbe8f8a6fbc6d709427c4a`)
- Python 3.12+ : `pip install pillow numpy capstone websocket-client pycdlib`
- EBOOT 복호화 도구(예: eboot_decrypt), 글꼴 `NanumSquareNeo-*.ttf`, `SeoulHangang*.ttf`, PPSSPP의 `assets/flash0/font/jpn0.pgf`

## 폴더 구성
```
<작업 폴더>/
  Gachitora! Abarenbou Kyoushi in High School (Japan).iso
  NanumSquareNeo-*.ttf, SeoulHangang*.ttf
  tools/            (이 저장소의 tools)
  trans/            db.json, out/b*.json, fix.json, eboot_kr.json, images*.json, images/*.json  (번역 — 저장소 미포함)
  work/
```

## 순서
1. ISO 추출: pycdlib로 `PSP_GAME`(INSDIR·MOVIE·sound 제외)을 `work/iso/` 에, `USRDIR/INSTMP` 를 `work/instmp/` 에 풉니다.
2. EBOOT 복호화: `eboot_decrypt work/iso/PSP_GAME/SYSDIR/EBOOT.BIN work/eboot_dec.elf`
3. 문자열 추출: `python tools/extract.py` → `trans/db.json`, `work/occ.json`
4. 번역 작성: `trans/out/bNNN.json` = `{id: 한국어}`. 검사: `python tools/check_batch.py all`
5. 그림 글자: `python tools/dump_tex.py` 로 PNG 추출, 사양 작성, `python tools/imgtext.py preview <해시>` 로 확인
6. 빌드: `python tools/build.py` → `Gachitora! Abarenbou Kyoushi in High School (Korean).iso`
7. 남은 일본어 검사: `python tools/audit_text.py`
8. 차분: `xdelta3 -e -0 -s 원본.iso 한글.iso 패치.xdelta`
