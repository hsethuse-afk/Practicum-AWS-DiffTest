# StrategySynthesizer Flow Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        StrategySynthesizer                          │
│                                                                     │
│  ┌──────────────┐              ┌─────────────────┐                │
│  │TypeDiscoverer│              │ StrategyConfig  │                │
│  │  (discovers  │              │  (config for    │                │
│  │  param types)│              │   strategies)   │                │
│  └──────────────┘              └─────────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
```

## Parameter Flow - create_strategy() Method

```
INPUT: func, param_hints (optional), test_file (optional)
  │
  ├─────────────────────────────────────────────────────────┐
  │                                                         │
  ▼                                                         │
┌─────────────────────────────────────────┐                │
│  1. TypeDiscoverer.discover_param_types │                │
│     - Checks function annotations       │                │
│     - Runs RightTyper inference         │                │
│     - Applies manual hints              │                │
└─────────────────────────────────────────┘                │
  │                                                         │
  │ Returns: Dict[param_name, type]                        │
  │                                                         │
  ▼                                                         │
┌─────────────────────────────────────────┐                │
│  2. For each parameter in signature:    │                │
│     - Get discovered type               │                │
│     - Call _create_strategy_from_type() │◄───────────────┘
│                                         │
└─────────────────────────────────────────┘
  │
  │ Collects: List[SearchStrategy]
  │
  ▼
┌─────────────────────────────────────────┐
│  3. Combine strategies into tuple       │
│     st.tuples(*strategies)              │
└─────────────────────────────────────────┘
  │
  │
  ▼
OUTPUT: StrategyPlan(arg_strategy=...)
```

## Type Processing Flow - _create_strategy_from_type()

```
INPUT: param_type, param_name
  │
  ├─────────────────┬──────────────────┬──────────────────┬─────────────────┐
  │                 │                  │                  │                 │
  ▼                 ▼                  ▼                  ▼                 ▼
┌─────────┐   ┌──────────┐   ┌──────────────┐   ┌─────────────┐   ┌──────────┐
│Is string│   │Is already│   │Is keyword    │   │Is type      │   │Fallback  │
│  type?  │   │SearchStr?│   │hint?         │   │annotation?  │   │          │
└─────────┘   └──────────┘   └──────────────┘   └─────────────┘   └──────────┘
  │                 │                  │                  │
  │                 │                  │                  │
  ▼                 ▼                  ▼                  ▼
_from_type_   Return as-is    _normalize_hint()   _from_annotation()
  string()                          │                    │
  │                                 │                    │
  │                                 ▼                    │
  │                        config.get_keyword_           │
  │                          strategy()                  │
  │                                                      │
  └──────────────────────────┬───────────────────────────┘
                             │
                             ▼
                    SearchStrategy
```

## _from_type_string() - String Type Parsing

```
INPUT: type_str (e.g., "list[int]", "dict[str, bool]")
  │
  ├──────────┬──────────┬──────────┬──────────┬─────────────┐
  │          │          │          │          │             │
  ▼          ▼          ▼          ▼          ▼             ▼
Basic    list[T]    set[T]    dict[K,V]  tuple[...]    Bare/Complex
"str"    pattern    pattern    pattern    pattern       "list", etc
"int"      │          │          │          │               │
"float"    │          │          │          │               │
"bool"     │          │          │          │               │
  │        │          │          │          │               │
  ▼        │          │          │          │               │
basic_type_│          │          │          │               │
  map      │          │          │          │               │
  │        │          │          │          │               │
  ▼        ▼          ▼          ▼          ▼               ▼
  │   ┌────────┐ ┌────────┐ ┌──────────┐ ┌──────┐    ┌─────────┐
  │   │Recursive│ │Recursive│ │Recursive │ │Fixed/│    │Fallback │
  │   │  parse │ │  parse │ │  parse   │ │Var   │    │registry │
  │   │  elem  │ │  elem  │ │  K & V   │ │length│    │ [Any]() │
  │   └────────┘ └────────┘ └──────────┘ └──────┘    └─────────┘
  │        │          │          │          │               │
  │        ▼          ▼          ▼          ▼               │
  │   st.lists() st.sets() st.dictionaries() st.tuples()    │
  │        │          │          │          │               │
  └────────┴──────────┴──────────┴──────────┴───────────────┘
                              │
                              ▼
                       SearchStrategy
```

## _from_annotation() - Type Annotation Processing

```
INPUT: annotation (e.g., List[int], Optional[str], Dict[str, Any])
  │
  ├─────────────┬────────────────┬─────────────┬──────────────┐
  │             │                │             │              │
  ▼             ▼                ▼             ▼              ▼
In registry?  Is Any?      Get origin      Is Union?    Try st.from_type()
  │             │          & args             │              │
  │             │             │                │              │
  ▼             ▼             │                ▼              ▼
Return        Return          │         Handle Optional   Fallback:
registry[T]() registry[Any]() │         or union types    one_of(int,
  │             │              │                │          float, str)
  │             │              │                │              │
  └─────────────┴──────────────┤                │              │
                               │                │              │
                               ▼                │              │
                      ┌─────────────────┐       │              │
                      │ Is List/Set/    │       │              │
                      │ Dict/Tuple?     │       │              │
                      └─────────────────┘       │              │
                               │                │              │
                ┌──────────────┼──────────┐     │              │
                │              │          │     │              │
                ▼              ▼          ▼     │              │
           List/Set      Dict[K,V]    Tuple    │              │
                │              │          │     │              │
                │              │          │     │              │
                ▼              ▼          ▼     │              │
         Recursive      Recursive    Fixed/    │              │
         process        process K&V  Variable  │              │
         element type   types        length    │              │
                │              │          │     │              │
                ▼              ▼          ▼     │              │
           st.lists()   st.dictionaries() st.tuples()         │
                │              │          │     │              │
                └──────────────┴──────────┴─────┴──────────────┘
                                 │
                                 ▼
                          SearchStrategy
```

## Component Interactions

```
┌─────────────────────────────────────────────────────────────────┐
│                     External Inputs                             │
└─────────────────────────────────────────────────────────────────┘
          │                    │                    │
          │                    │                    │
          ▼                    ▼                    ▼
   ┌────────────┐      ┌────────────┐      ┌────────────┐
   │  Function  │      │param_hints │      │ test_file  │
   │ signature  │      │  (manual)  │      │(RightTyper)│
   └────────────┘      └────────────┘      └────────────┘
          │                    │                    │
          └────────────────────┼────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ TypeDiscoverer   │
                    │ .discover_param_ │
                    │  types()         │
                    └──────────────────┘
                              │
                              ▼
                   Dict[param_name, type_info]
                              │
          ┌───────────────────┼────────────────────┐
          │                   │                    │
          ▼                   ▼                    ▼
    param1: int         param2: str         param3: List[int]
          │                   │                    │
          └───────────────────┼────────────────────┘
                              │
                              ▼
                ┌──────────────────────────┐
                │_create_strategy_from_type│
                │  (dispatches based on    │
                │   type representation)   │
                └──────────────────────────┘
                              │
          ┌───────────────────┼────────────────────┐
          │                   │                    │
          ▼                   ▼                    ▼
   st.integers()        st.text()           st.lists(st.integers())
          │                   │                    │
          └───────────────────┼────────────────────┘
                              │
                              ▼
                    st.tuples(*strategies)
                              │
                              ▼
                    ┌──────────────────┐
                    │  StrategyPlan    │
                    │  (final output)  │
                    └──────────────────┘
```

## Registry and Configuration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        StrategyConfig                           │
│                                                                 │
│  ┌──────────────────────┐      ┌──────────────────────────┐   │
│  │   Type Registry      │      │  Configuration Values    │   │
│  │                      │      │                          │   │
│  │  int → integers()    │      │  LIST_MAX_SIZE          │   │
│  │  str → text()        │      │  DICT_MAX_SIZE          │   │
│  │  float → floats()    │      │  SET_MAX_SIZE           │   │
│  │  bool → booleans()   │      │  TUPLE_MAX_SIZE         │   │
│  │  Any → one_of(...)   │      │  INT_MIN, INT_MAX       │   │
│  │  ...                 │      │  STRING_MAX_SIZE        │   │
│  └──────────────────────┘      └──────────────────────────┘   │
│           │                              │                     │
│           │                              │                     │
└───────────┼──────────────────────────────┼─────────────────────┘
            │                              │
            ▼                              ▼
   Used in registry[type]()     Used as max_size parameters
   lookups throughout code       in strategy generation
```

## Example: Processing `def add(x: int, y: List[str])`

```
Step 1: create_strategy() receives function
  │
  ▼
Step 2: TypeDiscoverer.discover_param_types()
  │
  ├─→ x: int (from annotation)
  └─→ y: List[str] (from annotation)
  │
  ▼
Step 3: For each parameter, call _create_strategy_from_type()
  │
  ├─→ x: int
  │   └─→ _from_annotation(int)
  │       └─→ registry[int]() → st.integers(min_value=INT_MIN, max_value=INT_MAX)
  │
  └─→ y: List[str]
      └─→ _from_annotation(List[str])
          ├─→ origin = list, args = [str]
          ├─→ Recursive: _from_annotation(str)
          │   └─→ registry[str]() → st.text(max_size=STRING_MAX_SIZE)
          └─→ st.lists(st.text(), max_size=LIST_MAX_SIZE)
  │
  ▼
Step 4: Combine strategies
  │
  st.tuples(
    st.integers(min_value=INT_MIN, max_value=INT_MAX),
    st.lists(st.text(max_size=STRING_MAX_SIZE), max_size=LIST_MAX_SIZE)
  )
  │
  ▼
Step 5: Return StrategyPlan
  │
  StrategyPlan(arg_strategy=<combined tuple strategy>)
```

## Key Decision Points

```
┌──────────────────────────────────────────────────────────────┐
│              Type Input Decision Tree                        │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
                Is input a string?
                    /        \
                  Yes         No
                  /             \
                 ▼               ▼
        _from_type_string()   Is SearchStrategy?
                                  /        \
                                Yes         No
                                /             \
                               ▼               ▼
                          Return it      Is keyword hint?
                                            /        \
                                          Yes         No
                                          /             \
                                         ▼               ▼
                                _normalize_hint()  _from_annotation()
```
