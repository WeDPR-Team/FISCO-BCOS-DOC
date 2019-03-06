# 构建第一个区块链应用

本章将会介绍一个基于FISCO BCOS区块链的业务应用场景开发全过程，从业务场景分析，到合约的设计实现，然后介绍合约编译以及如何部署到区块链，最后介绍一个应用模块的实现，通过我们提供的Web3SDK实现对区块链上合约的调用访问。

本教程要求用户熟悉Linux操作环境，具备Java开发的基本技能，能够使用Gradle工具，熟悉Solidity语法。通过学习教程，你将会了解到以下内容：

1. 如何将一个业务场景的逻辑用合约的形式表达
2. 如何将Solidity合约转化成Java类
3. 如何配置Web3SDK
4. 如何构建一个应用，并集成Web3SDK到应用工程
5. 如何通过Web3SDK调用合约接口，了解Web3SDK调用合约接口的原理

最后，教程中会提供示例的完整项目源码，用户可以在此基础上快速开发自己的应用。

```eval_rst
.. important::
    请参考 `安装文档 <../installation.html>`_ 完成FISCO BCOS区块链的搭建和控制台的下载工作。
```

## 示例应用需求

区块链天然具有防篡改，可追溯等特性，这些特性决定其更容易受金融领域的青睐，本文将会提供一个简易的资产管理的开发示例，并最终实现以下功能：
- 能够在区块链上进行资产注册
- 能够实现不同账户的转账
- 可以查询账户的资产金额

## 合约设计与实现

在区块链上进行应用开发时，结合业务需求，首先需要设计对应的智能合约，确定合约需要储存的数据，在此基础上确定智能合约对外提供的接口，最后给出各个接口的具体实现。

### 存储设计 

FISCO BCOS提供[CRUD合约](../manual/smart_contract.html#crud)开发模式，可以通过合约创建表，并对创建的表进行增删改查操作。针对本应用需要设计一个存储资产管理的表`t_asset`，该表字段如下：
- account: 主键，资产账户(字符串类型)
- asset_value: 资产金额(整形)

其中account是主键，即操作`t_asset`表时需要传入的字段，区块链根据该主键字段查询表中匹配的记录。`t_asset`表示例如下：

| account  | asset_value |
-----------|-------------
|   Alice  |   10000     |
|    Bob   |   20000     |

### 接口设计

 按照业务的设计目标，需要实现资产注册，转账，查询功能，对应功能的接口如下：
```solidity
// 查询资产金额
function select(string account) public constant returns(int256, uint256) 
// 资产注册
function register(string account, uint256 amount) public returns(int256)
// 资产转移
function transfer(string from_asset_account, string to_asset_account, uint256 amount) public returns(int256)
```

### 完整源码
```solidity
pragma solidity ^0.4.25;

import "./Table.sol";

contract Asset {

    event RegisterEvent(int256 ret, string account, uint256 amount);
    event TransferEvent(int256 ret, string from_account, string to_account, uint256 amount);
    
    constructor() public {
        createTable();
    }

    function createTable() private {
        TableFactory tf = TableFactory(0x1001); 
        // 资产管理表, key : account, field : asset_value
        // |  资产账户(主键)      |     资产金额       |
        // |-------------------- |-------------------|
        // |        account      |    asset_value    |     
        // |---------------------|-------------------|
        //
        // 创建表
        tf.createTable("t_asset", "account", "asset_value");
    }

    function openTable() private returns(Table) {
        TableFactory tf = TableFactory(0x1001);
        Table table = tf.openTable("t_asset");
        return table;
    }

    /*
    描述 : 根据资产账户查询资产金额
    参数 ： 
            account : 资产账户

    返回值：
            第一个参数： 成功返回0, 账户不存在返回-1
            第二个参数： 第一个参数为0时有效，资产金额
    */
    function select(string account) public constant returns(int256, uint256) {

        Table table = openTable();
        Condition condition = table.newCondition();
        condition.EQ("account", account);
        
        Entries entries = table.select(account, table.newCondition());
        uint256 amount = 0;
        if (0 == uint256(entries.size())) {
            return (-1, amount);
        } else {
            Entry entry = entries.get(0);
            return (0, uint256(entry.getInt("asset_value")));
        }
    }

    /*
    描述 : 资产注册
    参数 ： 
            account : 资产账户
            amount  : 资产金额
    返回值：
            0  资产注册成功
            -1 资产账户已存在
            -2 其他错误
    */
    function register(string account, uint256 amount) public returns(int256){
        int256 ret_code = 0;
        int256 ret= 0;
        uint256 asset_value = 0;
        (ret, asset_value) = select(account);
        if(ret != 0) {
            Table table = openTable();
            //插入
            Entry entry = table.newEntry();
            entry.set("account", account);
            entry.set("asset_value", int256(amount));

            int count = table.insert(account, entry);
            if (count == 1) {
                ret_code = 0;
            } else {
                ret_code = -2;
            }
        } else {
            //资产账户已存在
            ret_code = -1;
        }

        emit RegisterEvent(ret_code, account, amount);

        return ret_code;
    }

    /*
    描述 : 资产转移
    参数 ： 
            from_account : 转移资产账户
            to_account ： 接收资产账户
            amount ： 转移金额
    返回值：
            0  资产转移成功
            -1 转移资产账户不存在
            -2 接收资产账户不存在
            -3 金额不足
            -4 金额溢出
            -5 其他错误
    */
    function transfer(string from_account, string to_account, uint256 amount) public returns(int256) {
        // 查询转移资产账户信息
        int ret_code = 0;
        int256 ret = 0;
        uint256 from_asset_value = 0;
        uint256 to_asset_value = 0;
        
        (ret, from_asset_value) = select(from_account);
        if(ret != 0) {
            ret_code = -1;
            //转移资产的账户不存在
            emit TransferEvent(ret_code, from_account, to_account, amount);
            return ret_code;

        }

        // 查询接收资产账户信息
        (ret, to_asset_value) = select(to_account);
        if(ret != 0) {
            ret_code = -2;
            //接收资产的账户不存在
            emit TransferEvent(ret_code, from_account, to_account, amount);
            return ret_code;
        }

        if(from_asset_value < amount) {
            ret_code = -3;
            //转移资产的账户金额不足
            emit TransferEvent(ret_code, from_account, to_account, amount);
            return ret_code;
        } 

        if (to_asset_value + amount < to_asset_value) {
            ret_code = -4;
            //接收资产的账户金额溢出
            emit TransferEvent(ret_code, from_account, to_account, amount);
            return ret_code;
        }

        Table table = openTable();
        Condition condition0 = table.newCondition();
        condition0.EQ("account", from_account);

        //插入
        Entry entry0 = table.newEntry();
        entry0.set("account", from_account);
        entry0.set("asset_value", int256(from_asset_value - amount));
        
        int count = table.update(from_account, entry0, condition0);
        if(count != 1) {
            ret_code = -5;
            //更新错误
            emit TransferEvent(ret_code, from_account, to_account, amount);
            return ret_code;
        }

        Condition condition1 = table.newCondition();
        condition1.EQ("account", to_account);

        Entry entry1 = table.newEntry();
        entry1.set("account", to_account);
        entry1.set("asset_value", int256(to_asset_value + amount));
        table.update(to_account, entry1, condition1);

        emit TransferEvent(ret_code, from_account, to_account, amount);

        return ret_code;

    }
}
```
 **注：** `Asset.sol`合约的实现需要引入FISCO BCOS提供的一个系统合约接口文件 `Table.sol` ，该系统合约文件中的接口由FISCO BCOS底层实现。当业务合约需要操作CRUD接口时，均需要引入该接口合约文件。`Table.sol` 合约详细接口[参考这里](../manual/smart_contract.html#crud)。

**小结：** 我们根据业务需求设计了合约`Asset.sol`的存储与接口，并给出了完整实现。java应用需要调用合约时，需要首先将solidity文件转换为Java合约文件，这是下一步需要的工作。

## 合约编译
控制台提供了合约编译工具。将`Asset.sol Table.sol`存放在`console/tools/contracts`目录，利用console/tools目录下提供的`sol2java.sh`脚本执行合约编译，命令如下：
```bash
# 切换到fisco/console/tools目录
$ cd ~/fisco/console/tools/
# 编译合约，后面指定一个Java的包名参数，可以根据实际项目路径指定包名
$ ./sol2java.sh org.fisco.bcos.asset.contract
```
运行成功之后，将会在console/tools目录生成java、abi和bin目录，如下所示。
```bash
|-- abi // 编译生成的abi目录，存放solidity合约编译的abi文件
|   |-- Asset.abi
|   |-- Table.abi
|-- bin // 编译生成的bin目录，存放solidity合约编译的bin文件
|   |-- Asset.bin
|   |-- Table.bin
|-- contracts // 存放solidity合约源码文件，将需要编译的合约拷贝到该目录下
|   |-- Asset.sol // 拷贝进来的Asset.sol合约，依赖Table.sol
|   |-- Table.sol // 默认提供的系统CRUD合约接口文件
|-- java  // 存放编译的包路径及Java合约文件
|   |-- org
|        |--fisco
|             |--bcos
|                  |--asset
|                       |--contract
|                             |--Asset.java  // 编译成功的目标Java文件
|                             |--Table.java  // 编译成功的系统CRUD合约接口Java文件
|-- sol2java.sh
```
我们关注的是，java目录下生成了`org/fisco/bcos/asset/contract`包路径目录。包路径目录下将会生成Java合约文件`Asset.java`和`Table.java`，其中`Asset.java`是Java应用所需要的Java合约文件。

**小结：** 我们通过控制台合约编译工具将设计的`Asset.sol`合约编译为了`Asset.java`，下一步将进入SDK的配置与业务的开发。

## SDK配置

我们提供了一个Java工程项目供开发使用，首先获取Java工程项目：
```
# 获取Java工程项目压缩包
$ cd ~
$ curl -LO https://github.com/FISCO-BCOS/LargeFiles/raw/master/tools/asset-app.tar.gz
# 解压得到Java工程项目asset-app目录
$ tar -zxf asset-app.tar.gz
```
asset-app项目的目录结构如下：
```bash
|-- build.gradle // gradle配置文件
|-- gradle
|   |-- wrapper
|       |-- gradle-wrapper.jar // 用于下载Gradle的相关代码实现
|       |-- gradle-wrapper.properties // wrapper所使用的配置信息，比如gradle的版本等信息
|-- gradlew // Linux或者Unix下用于执行wrapper命令的Shell脚本
|-- gradlew.bat // Windows下用于执行wrapper命令的批处理脚本
|-- settings.gradle
|-- src
|   |-- main
|   |   |-- java
|   |         |-- org
|   |             |-- fisco
|   |                   |-- bcos
|   |                         |-- asset
|   |                               |-- client // 放置客户端调用类
|   |                                      |-- AssetClient.java
|   |                               |-- contract // 放置Java合约类
|   |                                      |-- Asset.java
|   |-- test 
|       |-- java 
|       |-- resources // 存放代码资源文件
|           |-- applicationContext.xml // 项目配置文件
|           |-- ca.crt // 区块链ca证书
|           |-- node.crt // 区块链ca证书
|           |-- node.key // 节点证书
|           |-- contract.properties // 存储部署合约地址的文件
|           |-- log4j.properties // 日志配置文件
|           |-- contract //存放solidity约文件
|                   |-- Asset.sol
|                   |-- Table.sol
|
|-- tool
    |-- asset_run.sh // 项目运行脚本
```

### 项目引入SDK
**项目的`build.gradle`文件已引入SDK，不需修改**。其引入方法介绍如下：
- SDK引入了以太坊的solidity编译器相关jar包，因此在`build.gradle`文件需要添加以太坊的远程仓库：
```java
repositories {
    maven {
        url "http：//maven.aliyun.com/nexus/content/groups/public/"
    }
    maven { url "https：//dl.bintray.com/ethereum/maven/" }
    mavenCentral()
}
```
- 引入SDK jar包，增加如下依赖：
```java
compile ('org.fisco-bcos：web3sdk：2.0.2')
```

### 证书与配置文件
- **区块链节点证书配置：**  
```bash
# 进入~/fisco目录
# 拷贝节点证书到项目的资源目录
$ cd ~
$ cp fisco/nodes/127.0.0.1/sdk/* asset-app/src/test/resources/
```

- `asset-app/src/test/resources/applicationContext.xml`是从fisco/nodes/127.0.0.1/sdk/复制而来，已默认配置好，不需要做额外修改。若搭建区块链节点时，```channel_listen_port```配置被改动，需要同样修改配置`applicationContext.xml`，具体请参考[SDK使用文档](../sdk/api_configuration.html#spring)。

**小结：** 我们为应用配置好了SDK，下一步将进入实际业务开发。

## 业务开发
**asset-app项目已经包含示例的完整源码，用户可以直接使用**，现在分别介绍Java类的设计与实现。

`Asset.java`： 通过控制台编译工具由`Asset.sol`文件生成，提供了solidity合约接口对应的Java接口，路径`/src/main/java/org/fisco/bcos/asset/contract`，Asset.java的主要接口：
```java
package org.fisco.bcos.asset.contract;

public class Asset extends Contract {
    // Asset.sol合约 transfer接口生成， 同步调用
    public RemoteCall<TransactionReceipt> transfer(String from_asset_account, String to_asset_account, BigInteger amount);
    // Asset.sol合约 transfer接口生成， 异步调用
    public void transfer(String from_asset_account, String to_asset_account, BigInteger amount, TransactionSucCallback callback);

    // Asset.sol合约 register接口生成， 同步调用
    public RemoteCall<TransactionReceipt> register(String asset_account, BigInteger amount);
    // Asset.sol合约 register接口生成， 异步调用
    public void register(String asset_account, BigInteger amount, TransactionSucCallback callback);
    // Asset.sol合约 select接口生成
    public RemoteCall<Tuple2<BigInteger, BigInteger>> select(String asset_account);

    // 加载Asset合约地址，生成Asset对象
    public static Asset load(String contractAddress, Web3j web3j, Credentials credentials, ContractGasProvider contractGasProvider);

    // 部署Assert.sol合约，生成Asset对象
    public static RemoteCall<Asset> deploy(Web3j web3j, Credentials credentials, ContractGasProvider contractGasProvider);
}
```
其中load与deploy函数用于构造Asset对象，其他接口分别用来调用对应的solidity的接口

`AssetClient.java`：入口类，通过调用`Asset.java`实现对合约的部署与调用，路径`/src/main/java/org/fisco/bcos/asset/client`，初始化以及调用流程都在该类中进行。
- 初始化  
初始化代码的主要功能为构造Web3j与Credentials对象，这两个对象在创建对应的合约类对象(调用合约类的deploy或者load函数)时需要使用。
```java
// function initialize
ApplicationContext context = new ClassPathXmlApplicationContext("classpath:applicationContext.xml");
Service service = context.getBean(Service.class);
service.run();

ChannelEthereumService channelEthereumService = new ChannelEthereumService();
channelEthereumService.setChannelService(service);
// init Web3j
Web3j web3j = Web3j.build(channelEthereumService, 1);
// init Credentials
Credentials credentials = Credentials.create(Keys.createEcKeyPair());
```
- 构造合约类对象  

可以使用deploy或者load函数初始化合约对象，两者使用场景不同，前者适用于初次部署合约，后者在合约已经部署并且已知合约地址时使用。
```java
// 部署合约
Asset asset = Asset.deploy(web3j, credentials, new StaticGasProvider(gasPrice, gasLimit)).send();
// 加载合约地址
Asset asset = Asset.load(contractAddress, web3j, credentials, new StaticGasProvider(gasPrice, gasLimit));
```

- 接口调用  

使用合约对象调用对应的接口，处理返回结果。
```java
// select接口调用
Tuple2<BigInteger, BigInteger> result = asset.select(assetAccount).send();
// register接口调用
TransactionReceipt receipt = asset.register(assetAccount, amount).send();
// transfer接口
TransactionReceipt receipt = asset.transfer(fromAssetAccount, toAssetAccount, amount).send();
```

**小结：** 通过Java合约文件，设计了一个业务Service类和调用入口类，已完资产管理的业务功能。接下来可以运行项目，测试功能是否正常。

## 运行
编译项目。
```bash
# 切换到项目目录
$ cd ~/asset-app
# 编译项目
$ ./gradlew build
```
编译成功之后，将在项目根目录下生成`dist`目录。dist目录下有一个`asset_run.sh`脚本，简化项目运行。现在开始一一验证本文开始定下的需求。

- 部署`Asset.sol`合约
```bash
# 进入dist目录
$ cd dist
$ bash asset_run.sh deploy
deploy Asset success, contract address is 0x23461960a54ec0d41e82631e92118bab12bc8a04
```
- 注册资产
```bash
$ bash asset_run.sh register Alice 999999999
register asset account success => asset: Alice, value: 999999999
$ bash asset_run.sh register Bob 111111111
register asset account success => asset: Bob, value: 111111111 
```
- 查询资产
```bash
$ bash asset_run.sh query Alice              
asset account Alice, value 999999999
$ bash asset_run.sh query Bob              
asset account Bob, value 111111111
```
- 资产转移
```bash
$ bash asset_run.sh transfer Alice Bob  555555
transfer success => from_asset: Alice, to_asset: Bob, amount: 555555 
$ bash asset_run.sh query Alice 
asset account Alice, value 999444444 
$ bash asset_run.sh query Bob
asset account Bob, value 111666666
```

**总结：** 至此，我们通过合约开发，合约编译，SDK配置与业务开发构建了一个基于FISCO BCOS联盟区块链的应用。