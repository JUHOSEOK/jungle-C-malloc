# Malloc Lab Optimization Tasks

현재 상태 요약

- allocator 구조: implicit free list
- fit 정책: first fit
- split: 사용 중
- coalescing: immediate
- realloc: `malloc -> memcpy -> free`
- correctness: 통과
- 기본 trace valid: 전부 yes
- 현재 perf index: 약 71
- 주요 병목 추정: throughput, 특히 `binary`, `binary2`

이 문서의 목표

- correctness를 유지하면서 작은 작업부터 점진적으로 성능을 개선한다.
- 먼저 현재 구조에서 올릴 수 있는 점수를 최대한 올린다.
- 그 다음 explicit free list 전환이 필요한지 판단한다.

---

## Phase 0. 기준선 고정

### Task 0-1. 현재 점수 기록

- [x] 현재 `mdriver` 전체 결과를 기록한다.
- [x] trace별 util / throughput / perf index를 따로 메모한다.
- [x] 특히 `binary`, `binary2`, `realloc` 관련 trace 결과를 따로 적는다.

기록할 것

- 전체 perf index
- trace별 valid
- trace별 util
- trace별 secs 또는 throughput

완료 기준

- 수정 전 baseline이 남아 있다.

---

## Phase 1. 코드 정리와 안전한 소규모 개선

### Task 1-1. `adjust_block_size` helper 추가

- [x] 요청 크기를 실제 block size로 맞추는 로직을 helper 함수로 분리한다.
- [ ] `mm_malloc`과 이후 `mm_realloc`에서 같은 helper를 쓰게 만든다.

대상 함수

- `mm_malloc`
- `mm_realloc`
- 새 helper: `static size_t adjust_block_size(size_t size);`

기대 효과

- 직접적인 점수 상승은 작음
- size 계산 실수를 줄여 correctness 유지에 도움

완료 기준

- size rounding 로직이 한 군데로 모인다.

### Task 1-2. `extend_heap`/`coalesce`/`place` 코드 정리

- [x] 불필요하거나 위험한 코드 조각을 제거한다.
- [ ] 경계 조건을 다시 점검한다.
- [ ] 함수마다 “입력 시점 invariants / 출력 시점 invariants”를 짧게 주석으로 남긴다.

체크 포인트

- `extend_heap`의 epilogue 처리
- `coalesce`의 4가지 case
- `place`의 split 후 남은 block 크기 조건

기대 효과

- 직접적인 성능 향상은 작음
- 이후 최적화 작업 시 버그 위험 감소

완료 기준

- 빌드가 깨끗하고, trace valid가 그대로 유지된다.

### Task 1-3. `find_fit` 탐색 시작점 명확화

- [ ] 현재 `find_fit`이 어디서부터 어디까지 순회하는지 주석으로 명확히 적는다.
- [ ] prologue부터 도는지, 첫 실제 block부터 도는지 의도를 분명히 한다.

기대 효과

- 성능 변화는 거의 없음
- 다음 단계인 next fit 적용이 쉬워짐

---

## Phase 2. 지금 구조에서 가장 먼저 먹히는 성능 개선

### Task 2-1. `mm_realloc` 빠른 반환 케이스 추가

- [x] `ptr == NULL`이면 `mm_malloc(size)` 호출
- [x] `size == 0`이면 `mm_free(ptr)` 후 `NULL` 반환
- [x] 새 요청 크기가 현재 block 안에 이미 들어가면 그대로 반환

대상 함수

- `mm_realloc`

필요 helper

- `static size_t adjust_block_size(size_t size);`

기대 효과

- throughput 개선
- 불필요한 `malloc + memcpy + free` 감소

완료 기준

- 기존 realloc correctness 유지
- 작은 크기 변경 realloc에서 불필요한 복사가 사라진다

### Task 2-2. `mm_realloc`의 in-place 확장

- [x] 다음 block이 free이고 합치면 충분한 경우 제자리 확장한다.
- [ ] 현재 block이 heap 끝이면 `extend_heap`으로 이어 붙여서 확장 가능한지 본다.
- [x] 확장 후 남는 공간이 충분하면 split한다.

대상 함수

- `mm_realloc`
- `coalesce`와 충돌하지 않게 block metadata 처리 확인

추가하면 좋은 helper

- `static int can_expand_into_next(void *bp, size_t asize);`
- `static void expand_into_next(void *bp, size_t asize);`

기대 효과

- throughput 크게 개선 가능
- utilization도 경우에 따라 좋아질 수 있음

완료 기준

- realloc trace에서 성능 개선이 보인다
- valid가 유지된다

### Task 2-3. `find_fit`을 next fit으로 전환

- [x] rover 포인터를 추가한다.
- [x] `find_fit`이 rover부터 탐색하고, 못 찾으면 앞부분을 다시 보게 만든다.
- [x] `coalesce` 또는 `place` 후 rover가 깨지지 않도록 보정한다.

대상 함수

- `mm_init`
- `find_fit`
- `coalesce`
- 필요 시 `place`

추가 전역

- `static char *rover;`

기대 효과

- throughput 개선
- 특히 긴 trace나 반복 alloc/free 패턴에서 탐색 비용 감소

주의

- utilization은 약간 나빠질 수 있음
- 점수가 오르는지 trace별 결과를 꼭 비교해야 함

완료 기준

- 전체 valid 유지
- `binary`, `binary2` 류 trace의 시간 감소 여부 확인

---

## Phase 3. implicit 구조에서 더 짜낼 수 있는 개선

### Task 3-1. split 정책 점검

- [ ] 남는 block이 최소 block size보다 작으면 split하지 않는다.
- [ ] 최소 block size가 현재 구조에 맞게 정의되어 있는지 확인한다.
- [ ] 너무 작은 free block이 많이 생기지 않는지 본다.

대상 함수

- `place`

기대 효과

- utilization 개선 가능
- 탐색 중 만나는 쓸모없는 작은 free block 감소

완료 기준

- trace valid 유지
- util 또는 throughput 둘 중 하나라도 개선

### Task 3-2. `mm_malloc`의 heap extension 정책 점검

- [ ] `MAX(asize, CHUNKSIZE)` 정책이 현재 trace에 맞는지 확인한다.
- [ ] `CHUNKSIZE`를 조금 키웠을 때 throughput이 좋아지는지 측정한다.
- [ ] util 손해가 큰지 같이 본다.

대상 매크로

- `CHUNKSIZE`

실험 후보

- `1 << 12`
- `1 << 13`
- `1 << 14`

기대 효과

- throughput 소폭 개선 가능
- util은 악화될 수 있음

완료 기준

- 숫자로 비교한 실험 결과가 있다

### Task 3-3. coalescing 비용과 효과 점검

- [ ] immediate coalescing이 실제로 도움이 되는지 trace 기준으로 본다.
- [ ] split/coalesce thrashing이 심한 trace가 있는지 확인한다.

메모할 것

- free 직후 다시 비슷한 크기로 alloc되는 패턴이 많은가
- immediate coalescing이 throughput을 깎는가

판단

- implicit free list에서는 coalescing을 늦추면 free block 수가 늘어 탐색이 더 느려질 수 있다
- 따라서 이 단계는 “무조건 변경”이 아니라 관찰 중심으로 진행한다

완료 기준

- immediate 유지가 맞는지, 조정이 필요한지 근거를 적는다

### Task 3-4. allocated block footer 제거 가능성 검토

- [ ] 현재 블록 포맷을 바꾸지 않고 유지할지 결정한다.
- [ ] `prev_alloc` 비트를 쓰는 방식으로 footer 제거가 가능한지 설계해본다.

영향

- utilization 개선 가능
- write 횟수 감소로 throughput도 약간 좋아질 수 있음

주의

- 구현 복잡도가 올라간다
- correctness 리스크가 next fit/realloc 최적화보다 큼

권장

- explicit free list 전환 전 마지막 선택지로 검토

---

## Phase 4. explicit free list 전환 판단

### Task 4-1. 전환 필요 여부 판단

- [ ] Phase 2~3 이후 perf index를 다시 측정한다.
- [ ] 목표 점수와 비교한다.

판단 기준

- 78~82 정도면 implicit에서 잘 끌어올린 편
- 85 이상을 안정적으로 노리면 explicit free list가 유력
- `binary`, `binary2`에서 여전히 느리면 explicit 전환 가치가 큼

완료 기준

- “implicit 유지” 또는 “explicit 전환” 결론을 적는다

---

## Phase 5. explicit free list 최소 구현

### Task 5-1. free block 포맷 설계

- [ ] free block payload에 `prev` / `next` 포인터를 저장하도록 구조를 정한다.
- [ ] 최소 free block size를 재정의한다.

필요 매크로 예시

- `PRED(bp)`
- `SUCC(bp)`

완료 기준

- free block layout이 문서나 주석으로 명확하다

### Task 5-2. free list helper 구현

- [ ] `insert_free_block`
- [ ] `remove_free_block`

권장 정책

- 일단 LIFO 삽입
- 구현이 가장 단순하고 빠름

완료 기준

- free list 조작 helper만 따로 테스트 가능할 정도로 분리됨

### Task 5-3. `coalesce`를 free list와 연결

- [ ] 병합 전 이웃 free block을 list에서 제거한다.
- [ ] 병합 후 결과 block을 list에 다시 넣는다.

대상 함수

- `coalesce`

완료 기준

- 병합 후 free list가 깨지지 않는다

### Task 5-4. `place`를 free list와 연결

- [ ] 할당 대상 free block을 list에서 제거한다.
- [ ] split되면 남은 free block을 list에 삽입한다.

대상 함수

- `place`

완료 기준

- free list 일관성이 유지된다

### Task 5-5. `find_fit`를 free list 기반으로 변경

- [ ] 전체 힙 순회 대신 free list만 순회한다.
- [ ] 처음에는 first fit on explicit list로 시작한다.

기대 효과

- throughput 크게 개선 가능

완료 기준

- 전체 trace valid 유지
- throughput 수치가 의미 있게 상승

---

## Phase 6. explicit free list 고도화

### Task 6-1. free list 삽입 정책 비교

- [ ] LIFO
- [ ] address-ordered

비교 포인트

- LIFO는 throughput에 유리한 편
- address-ordered는 coalescing/fragmentation 관점에서 장점이 있을 수 있음

완료 기준

- 한 가지 정책을 실험 결과로 선택한다

### Task 6-2. explicit에서도 `realloc` 최적화 유지

- [ ] next free block 흡수
- [ ] heap end 확장
- [ ] shrink 시 필요하면 split

완료 기준

- realloc이 explicit 구조와 잘 맞물린다

---

## Phase 7. segregated free list 필요 여부 판단

### Task 7-1. explicit 이후 점수 확인

- [ ] explicit free list 적용 후 perf index 재측정

판단 기준

- 목표가 85 전후면 explicit에서 멈춰도 충분할 수 있음
- 더 높은 throughput이 필요하고, 특정 크기대 요청이 많은 trace에서 병목이 남으면 seglist 검토

### Task 7-2. seglist 최소 설계

- [ ] size class 개수를 정한다
- [ ] `get_list_index(size)` helper를 만든다
- [ ] 각 class에 대해 explicit list를 하나씩 둔다

권장 시작안

- 16
- 32
- 64
- 128
- 256
- 512
- 1024
- 2048
- 4096+

완료 기준

- class 배치 원칙이 정리되어 있다

---

## 추천 실행 순서

아래 순서대로 진행하는 것을 권장한다.

- [ ] Task 0-1. 기준선 기록
- [ ] Task 1-1. `adjust_block_size` helper 추가
- [ ] Task 1-2. `extend_heap`/`coalesce`/`place` 정리
- [ ] Task 2-1. `realloc` 빠른 반환
- [ ] Task 2-2. `realloc` in-place 확장
- [ ] Task 2-3. next fit
- [ ] Task 3-1. split 정책 점검
- [ ] Task 3-2. `CHUNKSIZE` 실험
- [ ] Task 4-1. explicit 전환 여부 판단
- [ ] 필요 시 Phase 5 진입

---

## 내 상황에서의 현실적인 목표

- implicit + 작은 최적화만 적용: 75~82
- implicit에서 잘 다듬고 footer 최적화까지 하면: 80~85 근처 가능
- explicit free list로 안정 전환: 85~92 가능성 높음

현재 목표 제안

- 1차 목표: implicit 상태에서 78~82
- 2차 목표: explicit free list로 85+

---

## 작업 로그

아래 형식으로 진행 상황을 남긴다.

### YYYY-MM-DD

- 변경한 task:
- 수정한 함수:
- 결과:
- perf index:
- 특이사항:
