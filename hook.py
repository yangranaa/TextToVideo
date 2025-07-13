# pids = [16284, 9820, 14276, 16188, 10872, 8800, 11100, 18480]
#
# import frida
#
#
# def on_message(message, data):
#     if message['type'] == 'error':
#         print("⚠️ 错误详情:", message['stack'])
#     else:
#         print("✅ 捕获成功:", message)
#
#
# # 替换为实际渲染进程 PID
# pid = 14276
#
# session = frida.attach(pid)
# script = session.create_script("""
# 'use strict';
#
# const BCryptEncrypt = Module.findExportByName('bcryptPrimitives.dll', 'BCryptEncrypt');
# const BCryptExportKey = Module.findExportByName('bcryptPrimitives.dll', 'BCryptExportKey');
#
# // 剪映 7.9.0 实际使用的 BLOB 类型
# const BCRYPT_JY_KEY_BLOB = 0x4B445359; // 'YKDS' 魔数
#
# Interceptor.attach(BCryptEncrypt, {
#     onEnter: function(args) {
#         // 严格遵循 Windows SDK 参数顺序
#         this.hKey = args[0];
#         this.pbInput = args[1];
#         this.cbInput = args[2].toInt32();
#         this.pbIV = args[4];
#         this.cbIV = args[5].toInt32();
#
#         // 初始化上下文
#         this.valid = true;
#         this.keyBlob = null;
#
#         // 1. 输入缓冲区验证
#         if (this.pbInput.isNull() || this.cbInput <= 0) {
#             console.warn('[!] 无效输入缓冲区');
#             this.valid = false;
#             return;
#         }
#
#         // 2. 安全读取明文数据
#         try {
#             this.inputData = Memory.readByteArray(this.pbInput, this.cbInput);
#         } catch (e) {
#             console.error(`读取输入数据失败: ${e}`);
#             this.valid = false;
#             return;
#         }
#
#         // 3. 安全读取 IV 数据
#         if (!this.pbIV.isNull() && this.cbIV === 16) { // 确认 IV 长度 16
#             try {
#                 this.ivData = Memory.readByteArray(this.pbIV, 16);
#             } catch (e) {
#                 console.error(`读取 IV 失败: ${e}`);
#             }
#         } else {
#             console.warn('[!] 无效 IV 参数');
#         }
#
#         // 4. 密钥导出逻辑 (剪映定制方案)
#         if (this.valid) {
#             const pcbResult = Memory.alloc(4);
#
#             // 第一次调用获取所需大小
#             const status1 = BCryptExportKey(
#                 this.hKey,
#                 ptr(0),
#                 BCRYPT_JY_KEY_BLOB,
#                 ptr(0),
#                 ptr(0),
#                 0,
#                 pcbResult,
#                 0
#             );
#
#             if (status1 === 0) {
#                 const size = pcbResult.readU32();
#                 const pbOutput = Memory.alloc(size);
#
#                 // 第二次调用导出密钥
#                 const status2 = BCryptExportKey(
#                     this.hKey,
#                     ptr(0),
#                     BCRYPT_JY_KEY_BLOB,
#                     ptr(0),
#                     pbOutput,
#                     size,
#                     pcbResult,
#                     0
#                 );
#
#                 if (status2 === 0) {
#                     this.keyBlob = Memory.readByteArray(pbOutput, size);
#                 } else {
#                     console.error(`密钥导出失败: 0x${status2.toString(16)}`);
#                 }
#             } else {
#                 console.error(`获取密钥长度失败: 0x${status1.toString(16)}`);
#             }
#         }
#     },
#
#     onLeave: function(retval) {
#         if (this.valid && this.keyBlob) {
#             send({
#                 type: 'jy_encrypt_data',
#                 key: Array.from(this.keyBlob),
#                 iv: this.ivData ? Array.from(this.ivData) : [],
#                 plaintext: Array.from(this.inputData)
#             });
#         }
#     }
# });
# """)
# script.on('message', on_message)
# script.load()
# input("操作剪映保存草稿后按 Enter 退出...")