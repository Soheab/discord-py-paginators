from typing import Any


class MyClass:
    def __init__(self) -> None:
        self.lol = 0

    @property
    def foo(self) -> Any:
        return self.lol

    @foo.setter
    def foo(self, value: Any) -> None:
        print("setting", value)
        self.lol = value


class BetterClass(MyClass):
    @property
    def foo(self) -> Any:
        return super().foo

    @foo.setter
    def foo(self, value: Any) -> None:
        MyClass.foo.__set__(self, value)


inst = BetterClass()
print("before", inst.foo)
inst.foo = 1
print("after", inst.foo)
inst.foo = 2
print("after", inst.foo)
