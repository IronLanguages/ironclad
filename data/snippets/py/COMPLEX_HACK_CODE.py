
def __complex__(self):
    return complex(float(self.real), float(self.imag))
_ironclad_class_attrs['__complex__'] = __complex__
