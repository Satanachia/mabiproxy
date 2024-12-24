from dataclasses import dataclass, field
import varint as varint

@dataclass
class Parameter:
    type: int
    content: bytearray
    name: str = field(init=False)

    def __post_init__(self) -> None:
        #define length of paramter type
        #print(f"enter parameter name constructor matching type: {self.type}")
        match self.type:
            case 0:
                self.name = "none"
            case 1:
                self.name = "byte"
            case 2:
                self.name = "short"
            case 3:
                self.name = "int"
            case 4:
                self.name = "long"
            case 5:
                self.name = "float"
            case 6:
                self.name = "string"
            case 7:
                self.name = "bin"
@dataclass
class Packet:
    debug: bool
    source: str
    data:bytes
    header: bytes = field(init=False)
    opCode: bytes = field(init=False)
    ID: bytes = field(init=False)
    parametersCount: int = field(init=False)
    parameters: list[Parameter] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.header = self.data[0:6]
        self.opCode = self.data[6:10]
        self.ID = self.data[10:18]

    #parse data into parameters
        #Get numberof paramaters (stored in packet as a header). if the header is missing the packet has 0 params
        #print(f"entering paramter constructor")
        self.msglenbytes = varint.decode_bytes(self.data[18:])
        if self.msglenbytes == 0: 
            self.msglen = 1
            self.paramCount = 0
            if self.debug:
                print(f"no parameters data less than 16 bytes")
        else:
            #Get our message length varint length in bytes so we know what offset our param count is
            self.msglen = varint.varint_len(self.msglenbytes)
            self.paramCount = varint.decode_bytes(self.data[(18 + self.msglen):])        
        if self.paramCount > 0:
            self.paramIndex = 19 + (varint.varint_len(self.paramCount))+self.msglen
            for i in range(self.paramCount):
                #print(f"matching param type: {self.data[self.paramIndex]}")
                #ccreate paramter based on type then move index to the next param
                match self.data[self.paramIndex]:
                        case 0: #None
                            self.parameters.append(Parameter(0,self.data[self.paramIndex]))
                            self.paramIndex += 1
                        case 1: #Byte
                            self.parameters.append(Parameter(self.data[self.paramIndex],self.data[self.paramIndex+1:self.paramIndex+2]))
                            self.paramIndex += 2
                            #print("appended byte")
                        case 2: #Short
                            self.parameters.append(Parameter(self.data[self.paramIndex],self.data[self.paramIndex+1:self.paramIndex+3]))
                            self.paramIndex += 3
                        case 3 | 5: #Int and Float
                            self.parameters.append(Parameter(self.data[self.paramIndex],self.data[self.paramIndex+1:self.paramIndex+5]))
                            self.paramIndex += 5
                        case 4: #Long
                            self.parameters.append(Parameter(self.data[self.paramIndex],self.data[self.paramIndex+1:self.paramIndex+9]))
                            self.paramIndex += 9
                        case 6 :# String
                            #string and bin have an extra byte to designate how much data is in the paramete
                            contentLength = int(self.data[self.paramIndex+1:self.paramIndex+3].hex(),16)
                            #print(f"contentlength: {contentLength}")
                            self.parameters.append(Parameter(self.data[self.paramIndex],self.data[self.paramIndex+3:self.paramIndex+contentLength+3]))
                            self.paramIndex += (contentLength + 3)
                            #print("appended string")
                        case 7 :# bin
                            #string and bin have an extra byte to designate how much data is in the paramete
                            contentLength = int(self.data[self.paramIndex+1:self.paramIndex+3].hex(),16)
                            #if the content length is 0 then we only hve 1 byte of info tacked on the end? might just be null too. 
                            if contentLength == 0:
                                self.parameters.append(Parameter(self.data[self.paramIndex],self.data[self.paramIndex+2:self.paramIndex+3]))
                                self.paramIndex += 4
                            self.parameters.append(Parameter(self.data[self.paramIndex],self.data[self.paramIndex+3:self.paramIndex+contentLength+3]))
                            self.paramIndex += (contentLength + 3)
                            #print("appended string")
                        case _:
                           if self.debug:
                            print("param match not found")

def parse(data, port, direction, debug):
    if port==0:
        return False
    if direction == 'send':
        return False
    if hex(data[0]) == hex(0x88): 
        if debug:
            print(f"Encrypted Packet: {direction} {data.hex()}")
        return False
    
    #hopefully this will fix issues of failed packets
    try: 
        packet = Packet(source = direction, data = data, debug = debug)
    except:
        return False
    
    if packet.opCode.hex()=='0001d4c3': #NGS recv 7045000000000001d4c3
        return False
    
    #check all parameters make sure they bytes, if not return false cause for some reason we failed to parse it
    for i in range(len(packet.parameters)):
        if type(packet.parameters[i].content) != bytes:
            return False
   
    if debug:
        print("[{}({})] {}".format(direction, port, data.hex()))
    
        print(f"\n{direction} - header: {packet.header.hex()} OPCode: {packet.opCode.hex()} ID: {packet.ID.hex()}")
        print(f"Total parameters: {packet.paramCount}")
        for i in range(len(packet.parameters)):
            print(f"Parameter{i} : [Type: '{packet.parameters[i].type}' Data(hex): '{''.join(f'/x{x:02x}' for x in packet.parameters[i].content)}' Name: '{packet.parameters[i].name}']")

    return packet
