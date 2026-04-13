# CS:APP Malloc Lab 한국어 가이드

이 문서는 [/workspaces/malloc_lab_docker/malloc-lab/README.md](/workspaces/malloc_lab_docker/malloc-lab/README.md)의 짧은 영어 안내를 한국어로 풀어쓴 문서이며, 이 프로젝트를 처음 공부하는 사람이 바로 시작할 수 있도록 프로젝트 분석과 학습 가이드를 함께 담고 있습니다.

## 1. 이 프로젝트는 무엇인가

이 프로젝트는 CS:APP(Computer Systems: A Programmer's Perspective)의 대표 과제인 `Malloc Lab`입니다. 목표는 C 표준 라이브러리의 `malloc`, `free`, `realloc`처럼 동작하는 **동적 메모리 할당기**를 직접 구현하는 것입니다.

학생이 직접 수정해야 하는 핵심 파일은 [/workspaces/malloc_lab_docker/malloc-lab/mm.c](/workspaces/malloc_lab_docker/malloc-lab/mm.c) 하나입니다. 나머지 파일들은 테스트 드라이버, 힙 시뮬레이터, 타이머, 트레이스 파일 등으로 구성되어 있고, 여러분이 작성한 할당기를 검증하고 성능을 측정합니다.

이 과제를 통해 보통 다음 개념을 깊게 익히게 됩니다.

- 힙 메모리 구조
- 블록 헤더와 푸터
- 정렬(alignment)
- 내부 단편화와 외부 단편화
- 블록 분할(split)과 병합(coalescing)
- `first fit`, `next fit`, `best fit`
- explicit free list, segregated free list 같은 자료구조 설계
- `realloc` 최적화

## 2. 기존 README의 핵심 내용 한국어 정리

원본 README의 핵심은 다음과 같습니다.

- `mm.c`, `mm.h`
  - 여러분이 구현할 malloc 패키지입니다.
  - 제출용으로 실제 수정하는 파일은 보통 `mm.c`입니다.
- `mdriver.c`
  - 여러분의 `mm.c` 구현을 테스트하는 드라이버입니다.
- `short1-bal.rep`, `short2-bal.rep`
  - 아주 작은 테스트용 trace 파일입니다.
  - 구현 초기 디버깅에 적합합니다.
- `Makefile`
  - 드라이버를 빌드합니다.
- `config.h`
  - 드라이버 동작과 성능 평가 관련 설정을 담습니다.
- `memlib.c`, `memlib.h`
  - 실제 운영체제의 `sbrk`를 흉내 내는 힙 시뮬레이터입니다.
- `fsecs`, `fcyc`, `ftimer`, `clock`
  - 성능 측정용 타이머 코드입니다.

빌드와 실행은 다음처럼 합니다.

```bash
cd /workspaces/malloc_lab_docker/malloc-lab
make
./mdriver -V -f short1-bal.rep
./mdriver -h
```

## 3. 프로젝트 전체 구조 분석

프로젝트를 기능별로 나누면 이렇게 볼 수 있습니다.

### 구현 대상

- [/workspaces/malloc_lab_docker/malloc-lab/mm.c](/workspaces/malloc_lab_docker/malloc-lab/mm.c)
  - 여러분이 직접 구현해야 하는 allocator입니다.
  - `mm_init`, `mm_malloc`, `mm_free`, `mm_realloc`를 정의합니다.
- [/workspaces/malloc_lab_docker/malloc-lab/mm.h](/workspaces/malloc_lab_docker/malloc-lab/mm.h)
  - allocator 인터페이스와 팀 정보 구조체가 정의되어 있습니다.

### 테스트와 평가

- [/workspaces/malloc_lab_docker/malloc-lab/mdriver.c](/workspaces/malloc_lab_docker/malloc-lab/mdriver.c)
  - trace 파일을 읽어 `malloc/free/realloc` 요청을 순서대로 재현합니다.
  - 올바르게 동작하는지 검사합니다.
  - 메모리 이용률(utilization)과 처리량(throughput)을 측정합니다.
- [/workspaces/malloc_lab_docker/malloc-lab/config.h](/workspaces/malloc_lab_docker/malloc-lab/config.h)
  - 기본 trace 목록, 정렬 단위, 최대 힙 크기, 성능 가중치 등을 정의합니다.

### 힙 시뮬레이션

- [/workspaces/malloc_lab_docker/malloc-lab/memlib.c](/workspaces/malloc_lab_docker/malloc-lab/memlib.c)
  - `mem_sbrk`로 힙을 늘립니다.
  - 실제 OS 메모리 대신, 큰 버퍼를 힙처럼 사용합니다.
  - allocator는 보통 이 파일의 API를 통해 새 힙 공간을 요청합니다.

### 입력 데이터

- [/workspaces/malloc_lab_docker/malloc-lab/short1-bal.rep](/workspaces/malloc_lab_docker/malloc-lab/short1-bal.rep)
- [/workspaces/malloc_lab_docker/malloc-lab/short2-bal.rep](/workspaces/malloc_lab_docker/malloc-lab/short2-bal.rep)
- [/workspaces/malloc_lab_docker/malloc-lab/traces](/workspaces/malloc_lab_docker/malloc-lab/traces)
  - allocator에 들어오는 요청 시나리오입니다.
  - `a`는 allocate, `r`은 realloc, `f`는 free를 의미합니다.
  - `*-bal.rep`는 각 할당이 결국 free되는 balanced trace입니다.

## 4. 현재 `mm.c` 상태

현재 저장소의 [/workspaces/malloc_lab_docker/malloc-lab/mm.c](/workspaces/malloc_lab_docker/malloc-lab/mm.c)는 **완성된 allocator가 아니라 기본 템플릿 수준의 naive 구현**입니다.

현재 구현의 특징은 다음과 같습니다.

- `mm_malloc`
  - 요청이 들어오면 기존 블록 재사용 없이 `mem_sbrk`로 힙 끝을 계속 늘립니다.
- `mm_free`
  - 아무 일도 하지 않습니다.
- `mm_realloc`
  - 새 블록을 다시 할당하고 데이터를 복사한 뒤 기존 블록을 `free`합니다.
  - 하지만 현재 `free`가 아무 일도 하지 않으므로 사실상 재사용이 없습니다.
- `mm_init`
  - 특별한 초기화가 없습니다.

즉, 이 구현은 개념 설명용 출발점일 뿐이고, 실제 과제 점수를 잘 받으려면 거의 새로 설계해야 합니다.

## 5. 이 과제에서 무엇이 평가되나

드라이버는 크게 두 가지를 봅니다.

- 정답성(correctness)
  - 겹치는 블록을 반환하면 안 됩니다.
  - 정렬이 맞아야 합니다.
  - `malloc`, `free`, `realloc` 동작이 trace와 일치해야 합니다.
- 성능(performance)
  - 공간 활용도(utilization): 힙을 얼마나 효율적으로 쓰는가
  - 처리량(throughput): 요청을 얼마나 빠르게 처리하는가

[/workspaces/malloc_lab_docker/malloc-lab/config.h](/workspaces/malloc_lab_docker/malloc-lab/config.h) 기준으로, 성능 지수는 다음 철학으로 계산됩니다.

- 공간 활용도 비중: `0.60`
- 처리량 비중: `0.40`

즉, 빠르기만 하고 메모리를 낭비하면 점수가 잘 안 나오고, 반대로 메모리만 아끼고 너무 느려도 좋은 점수를 받기 어렵습니다.

## 6. trace 파일은 왜 중요한가

`Malloc Lab`을 공부할 때 trace 파일은 사실상 테스트케이스이자 문제 설명입니다.

[/workspaces/malloc_lab_docker/malloc-lab/traces/README](/workspaces/malloc_lab_docker/malloc-lab/traces/README)를 보면 다음 의도를 알 수 있습니다.

- `short1`, `short2`
  - 아주 작은 디버깅용
- `coalescing`
  - free된 블록 병합이 제대로 되는지 검사
- `random`, `random2`
  - 랜덤 요청에서 정합성과 안정성 검사
- `binary`, `binary2`
  - 특정 크기 패턴에서 fit 전략 차이를 시험
- `realloc`, `realloc2`
  - `realloc` 구현이 너무 단순해서 불필요한 복사와 단편화를 만들지 않는지 검사
- `amptjp`, `cccp`, `cp-decl`, `expr`
  - 실제 프로그램에서 나온 패턴 기반 trace

즉, 이 프로젝트는 단순히 함수 4개를 채우는 문제가 아니라, 다양한 메모리 사용 패턴에 대해 allocator 설계를 검증하는 과제입니다.

## 7. 처음 공부할 때 추천하는 순서

처음부터 완성형 explicit list나 segregated list로 들어가면 어렵게 느껴질 수 있습니다. 보통 아래 순서가 가장 안정적입니다.

### 1단계: 힙 블록 구조 이해

먼저 아래 개념을 그림으로 그려 보면서 이해하는 것이 좋습니다.

- 정렬된 블록 크기
- 헤더에 들어갈 정보
- 할당 여부 비트
- 푸터의 역할
- 프롤로그 블록, 에필로그 블록

가장 먼저 이해해야 할 질문은 이것입니다.

- 블록 하나는 메모리에서 어떤 모양인가?
- 다음 블록의 시작 주소는 어떻게 계산하는가?
- free된 이웃 블록과 어떻게 합칠 수 있는가?

### 2단계: implicit free list 구현

가장 추천하는 입문 구현은 다음 조합입니다.

- 경계 태그(boundary tags)
- implicit free list
- first fit
- immediate coalescing
- block splitting

이 단계의 목표는 "고득점"이 아니라 "전체 구조를 직접 만들어 보는 것"입니다.

이 단계에서 보통 다음 함수들이 필요합니다.

- 힙 초기화
- 힙 확장
- free 블록 찾기
- 블록 배치
- 블록 분할
- 인접 free 블록 병합

### 3단계: heap checker 추가

과제에서 가장 시간을 많이 아끼는 도구는 `mm_checkheap` 같은 검사 함수입니다. 현재 템플릿에 반드시 들어 있지는 않더라도, 스스로 추가하는 것이 매우 좋습니다.

예를 들면 다음을 검사할 수 있습니다.

- 모든 블록이 정렬되어 있는가
- 헤더와 푸터 값이 일치하는가
- 연속된 free 블록이 병합되지 않고 남아 있지 않은가
- free list에 있는 블록이 실제로 free 상태인가
- 힙 범위를 벗어난 포인터가 없는가

### 4단계: `realloc` 개선

처음에는 단순 복사 방식으로 시작해도 됩니다. 하지만 점수를 높이려면 다음을 고민해야 합니다.

- 뒤쪽 블록이 비어 있으면 확장해서 제자리 재사용 가능할까
- 너무 큰 블록이면 분할할까
- 새 블록 복사가 꼭 필요한 경우만 복사할 수 있을까

### 5단계: explicit free list 또는 segregated free list

고득점을 노린다면 보통 여기까지 갑니다.

- explicit free list
  - free 블록들만 연결 리스트로 관리
  - implicit list보다 탐색 비용이 줄어듭니다.
- segregated free list
  - 크기별로 free list를 여러 개 운영
  - 처리량과 공간 효율을 더 잘 맞출 수 있습니다.

## 8. 실제 공부 방법

가장 추천하는 학습 방식은 "작게 구현하고, 작은 trace로 검증하고, 점점 넓히는 방식"입니다.

### 추천 루틴

1. `short1-bal.rep`만 통과시키기
2. `short2-bal.rep` 통과시키기
3. `coalescing-bal.rep` 통과시키기
4. 기본 trace 전체를 돌리기
5. 그 다음 성능 최적화하기

실행 예시는 다음과 같습니다.

```bash
cd /workspaces/malloc_lab_docker/malloc-lab
make
./mdriver -V -f short1-bal.rep
./mdriver -V -f short2-bal.rep
./mdriver -V -f traces/coalescing-bal.rep
./mdriver -v
```

### 공부하면서 꼭 해볼 것

- 블록 레이아웃을 종이에 직접 그려 보기
- `malloc`, `free`, `realloc` 한 번씩 호출될 때 힙이 어떻게 변하는지 추적하기
- 작은 크기, 큰 크기, 연속 free, 중간 realloc 케이스를 따로 생각해 보기
- segmentation fault가 나면 포인터 산술과 헤더/푸터 계산부터 의심하기

## 9. 구현 전략을 어떻게 선택할까

전략별 감각은 대략 이렇습니다.

- implicit free list
  - 가장 배우기 좋습니다.
  - 구현은 비교적 단순하지만 큰 trace에서 느릴 수 있습니다.
- explicit free list
  - free 블록만 순회하므로 더 실용적입니다.
  - 포인터 관리 실수가 잦아 디버깅 난이도는 올라갑니다.
- segregated free list
  - 점수 면에서 유리한 경우가 많습니다.
  - 설계와 디버깅이 가장 어렵습니다.

처음이라면 보통 아래 전략이 좋습니다.

1. implicit free list로 전체 구조 완성
2. heap checker로 안정화
3. explicit free list로 업그레이드
4. 여유가 있으면 segregated free list 고려

## 10. 현재 저장소에서 보이는 참고 사항

프로젝트를 살펴보면서 확인한 점입니다.

- `make`는 현재 정상적으로 동작합니다.
- 현재 `mm.c`는 예제용 naive allocator입니다.
- `./mdriver -V -f short1-bal.rep` 실행은 현재 통과합니다.
- 현재 [/workspaces/malloc_lab_docker/malloc-lab/mdriver.c](/workspaces/malloc_lab_docker/malloc-lab/mdriver.c)에는 `getopt returned: ...`를 출력하는 디버그용 `printf`가 들어 있어 실행 시 옵션 문자 코드가 함께 출력됩니다.

이 마지막 항목은 allocator 구현과 직접 관련은 없지만, 출력이 지저분하게 보이는 이유가 될 수 있습니다.

## 11. 이 프로젝트를 한 문장으로 요약하면

이 프로젝트는 "운영체제와 런타임이 해 주던 동적 메모리 관리를 직접 설계하고, 정확성과 성능 사이의 균형을 잡는 시스템 프로그래밍 훈련"이라고 볼 수 있습니다.

## 12. 시작할 때 가장 실용적인 체크리스트

- `mm.c`의 팀 정보부터 실제 정보로 바꾸기
- 블록 형식을 먼저 문서나 그림으로 정하기
- `mm_init`, `extend_heap`, `coalesce`, `find_fit`, `place` 같은 내부 보조 함수 설계하기
- 작은 trace부터 돌리기
- heap checker를 일찍 만들기
- 전체 trace 통과 후에 최적화하기

## 13. 다음에 무엇을 하면 좋나

이 문서를 읽은 뒤 바로 실습으로 이어가려면 다음 순서를 추천합니다.

1. `mm.c`를 naive 버전에서 implicit free list 버전으로 바꾸기
2. `free`와 `coalesce`를 먼저 안정화하기
3. `realloc`은 단순 구현으로 먼저 맞추기
4. 마지막에 탐색 전략과 free list 구조를 최적화하기

원하면 다음 단계로 이어서 `mm.c`의 기본 allocator 골격을 제가 직접 한국어 주석과 함께 만들어 드릴 수 있습니다.
