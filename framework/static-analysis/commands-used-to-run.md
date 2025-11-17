## 1. Running a single test case for a single method
```
uv run solutions/syntaxer.py 'jpamb.cases.Simple.assertPositive:(I)V'


uv run assert-aware-analysis/structure.py 'jpamb.cases.Simple.assertPositive:(I)V'
```
## 2. Running test cases for a single file (Simple.java file)
```
uv run jpamb test --filter "Simple" --with-python assert-aware-analysis/static-analysis/structure.py
```

## 3. Run all test files with UV
```
uv run jpamb test --with-python assert-aware-analysis/structure.py
```