-- 用户转账记录表
CREATE TABLE TransferRecords (
    Id INT PRIMARY KEY IDENTITY(1,1),
    OrderId VARCHAR(50) NOT NULL,
    TransferType VARCHAR(20) NOT NULL,
    Amount DECIMAL(18,2) NOT NULL,
    Status VARCHAR(10) NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE()
);

-- 查询失败的转账记录
SELECT 
    tr.OrderId,
    tr.TransferType,
    tr.Amount,
    tr.Status,
    tr.CreatedAt
FROM TransferRecords tr
WHERE tr.Status = 'failed'
    AND tr.TransferType = 'offmarket'
    AND tr.CreatedAt >= DATEADD(DAY, -7, GETDATE());

-- 更新转账状态
UPDATE TransferRecords 
SET Status = 'completed'
WHERE OrderId = @OrderId 
    AND Status = 'processing';

-- 获取场外转账统计
SELECT 
    COUNT(*) as TotalTransfers,
    SUM(CASE WHEN Status = 'failed' THEN 1 ELSE 0 END) as FailedTransfers,
    SUM(CASE WHEN Status = 'completed' THEN 1 ELSE 0 END) as CompletedTransfers
FROM TransferRecords 
WHERE TransferType = 'offmarket'
    AND CreatedAt >= DATEADD(MONTH, -1, GETDATE());