# 과제2를 한 단어로 돌리기 위한 Makefile.
# 컨테이너 안에서 실행한다 (Codespaces 터미널, 또는 docker compose exec lab bash).
#
#   make test        유닛 테스트 (tests/test_*.py)
#   make serve       단축 URL 웹 서버 (포트 8000)
#   make experiment  체이닝 적재율별 탐색 횟수 실험
#   make help        사용 가능한 명령 보기
#   make clean       캐시 정리
#
# 외부 라이브러리를 쓰지 않는다. Python 표준 모듈만으로 돈다.

PORT ?= 8000

.PHONY: all test serve experiment help clean

all: test

test:
	@python3 -m unittest discover -s tests -v

serve:
	@python3 -m src.server --port $(PORT)

experiment:
	@python3 -m experiments.chaining_experiment

help:
	@printf '%s\n' \
		'사용 가능한 명령:' \
		'  make test        유닛 테스트 실행' \
		'  make serve       URL 단축 웹 서버 실행 (기본 포트 8000)' \
		'  make experiment  체이닝 적재율별 탐색 횟수 실험' \
		'  make clean       Python 캐시 정리' \
		'  make help        이 도움말 표시' \
		'  PORT=8080 make serve  포트를 지정해 서버 실행'

clean:
	rm -rf src/__pycache__ tests/__pycache__ experiments/__pycache__
