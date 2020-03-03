class Utils():
    # hex into spaced & upper string
    def bytes_to_hex_str(self, bytesinput) -> str:
        # insert between string
        def insert_str(string, str_to_insert, index):
            return string[:index] + str_to_insert + string[index:]
        # make into string
        stroutput = bytesinput.hex()
        for i in range(int(len(str(bytesinput.hex()))/2-1)):
            stroutput = insert_str(stroutput, " ", 3*i+2)
        stroutput = stroutput.upper()
        return stroutput

    # 실수 체크
    def float_check(self, number, option=None) -> None:
        if not (isinstance(number, int) or isinstance(number, float)):
            is_float = False
        else:
            is_float = True
        if not is_float:
            if option:
                raise ValueError("Please enter float number, or \"" + str(option) + "\"!")
            else:
                raise ValueError("Please enter float number!")

    #  정수 체크
    def integer_check(self, number, option=None) -> None:
        if not isinstance(number, int):
            is_integer = False
        else:
            is_integer = True
        if not is_integer:
            if option:
                raise ValueError("Please enter integer number, or \"" + str(option) + "\"!")
            else:
                raise ValueError("Please enter integer number!")

    # 2바이트 헥스 리스트를 integer로 변환
    def twobyte_hexlist_to_int(self, byte1, byte2) -> int:
        return int(hex(byte1)[2:] + hex(byte2)[2:], 16)
    
    # 리스트로 변환
    def to_list(self, input_data) -> list:
        if isinstance(input_data, list) or isinstance(input_data, tuple):
            return list(input_data)
        elif isinstance(input_data, int) or isinstance(input_data, float) \
            or isinstance(input_data, str) or isinstance(input_data, bool) or input_data == None:
            return [input_data]
        else:
            raise ValueError("Error. Enter list, or tuple, or int, or float, or str, or bool, or None.")

    # 같은 원소가 있는지 확인
    def check_same_element(self, input_list) -> None:
        for i in range(len(input_list)-1):
            if input_list[i] in input_list[i+1:]:
                raise ValueError("All elements must be different each other in list.")

    # 모든 cube id가 있는지 확인
    def all_cube_in_check(self, input_list, connection_number) -> bool:
        for i in range(connection_number):
            check = (i in input_list) and True
        return check

    ### 리스트 포인터(id)를 다르게 복사
    def list_product_copy(self, input_list, number) -> list:
        input_list = input_list[0]
        out_list = []
        i = 0
        while i < number:
            new_list = [0]*len(input_list)
            for j in range(len(input_list)):
                new_list[j] = input_list[j]
            out_list.append(new_list)
            i += 1
        return out_list

    input_flag = False

    def input(self, string):
        Utils.input_flag = True

    def print(self, string, option=None):
        print(string)
        

    
