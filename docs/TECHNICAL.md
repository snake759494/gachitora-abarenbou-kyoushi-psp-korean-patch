# 기술 문서

## 디스크 구조
- `PSP_GAME/USRDIR/DATA/` : 2D UI(`2D/*.BIN`), 이벤트(`event_p/*.bin`), 장면 레이아웃(`layout/`), 미니게임, 스태프롤 등. 모두 `PSP\0` 컨테이너.
- `PSP_GAME/USRDIR/INSTMP/` : 스테이지·캐릭터 데이터의 평문 사본. `PSP_GAME/INSDIR/` 는 같은 데이터의 PGD 암호화본(설치 기능용).
- EBOOT는 암호화되어 있어 복호화한 평문 ELF로 교체합니다.

## 컨테이너 `PSP\0`
`magic, float 1.0, u32 count, u32 flag, (u32 offset, u32 size) * count` (오프셋은 컨테이너 시작 기준). 자식이 또 컨테이너일 수 있습니다. 리프를 키울 때는 리프 뒤에 0x80 단위로 공간을 끼워 넣고 모든 상위 컨테이너의 오프셋·크기를 고칩니다(`tools/pspc.py apply_mods`).

## 텍스트
- 모든 텍스트는 **UTF-16LE**. 제어 코드: `#w0.5f`(대기), `#s25.0f`(속도), `#cRRGGBBAA…#d`(색), `#p/#q/#Q + cir/cro/squ/tri/lef/rig/sel/sta`(버튼 아이콘), `#k`, `#rf`, `%d/%s` 등.
- **ZAR** (`ZAR\0` + `PSP\0` 헤더): u32@0x14 = 테이블 기준 B. B+4 = 레코드 수, B+0x20부터 8바이트 레코드 `(u16 flag, u16 len, u32 off)`. flag 0xffff = 문자열(len은 NUL 포함 글자 수, 위치 B+off), 그 밖은 그룹 헤더. 재작성 시 문자열 영역을 0x20 정렬로 다시 배치(`tools/zar.py`). 일부 ZAR은 1바이트 ASCII 키 테이블이라 제외.
- **TSB**(이벤트 스크립트): 대사 문자열은 TSB 기준 4바이트 오프셋 포인터로 참조됨. 원래 칸에 들어가면 제자리, 넘치면 TSB 끝에 붙이고 포인터를 바꿉니다(`tools/tsb.py`).
- **EBOOT**: UTF-16 문자열 풀은 원래 칸 크기 안에서 교체. 일부 문자열은 코드가 `ori rX,zero,<글자>` + `sh` 로 스택에 한 글자씩 만들기 때문에 명령어의 즉치값을 직접 바꿉니다(`eboot_patch.INLINE`).

## 글꼴
게임은 `sceFontOpen(lib, 0, …)` 으로 시스템 폰트 jpn0.pgf를 엽니다. 이 호출을 `sceFontOpenUserFile(lib, "disc0:/PSP_GAME/USRDIR/FONT.PGF", …)` 로 바꿨습니다(NID 교체 + 재배치 엔트리가 붙은 lui/addiu 위치를 유지한 채 코드 재배열, `tools/eboot_patch.py`). FONT.PGF는 jpn0.pgf에 나눔스퀘어네오 Bold 18px로 KS X 1001 한글 2,350자를 추가한 것입니다(`tools/build_font.py`).

## 그림
텍스처는 `MIG.00.1PSP` (GIM) 형식: RGBA5650/5551/4444/8888, 인덱스 4/8비트, 스위즐. `tools/mig.py` 로 디코드/인코드(인덱스 형식은 원래 팔레트에 최근접 색으로 맞춤). 텍스처는 md5 앞 12자리로 식별하고, 사양(JSON: 지울 상자, 글자, 글꼴, 색, 외곽선)으로 다시 그립니다(`tools/imgtext.py`). INSTMP 스테이지 파일은 시그니처 검색으로 텍스처를 찾아 같은 크기로 교체합니다.

## 설치 데이터
게임은 설치 여부와 관계없이 일부 데이터를 `INSDIR/` 에서 읽습니다. 암호화본은 고칠 수 없으므로 EBOOT의 경로 문자열 `INSDIR/` 을 같은 길이의 `INSTMP/` 로 바꿔 평문 사본을 읽게 했습니다.
