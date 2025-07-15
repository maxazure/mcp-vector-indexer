using System;
using System.Collections.Generic;

namespace TestApp
{
    public class OrderManager
    {
        public void ProcessOffmarketTransfer(Order order)
        {
            try
            {
                // 处理场外转账
                if (order.TransferType == "offmarket")
                {
                    ValidateTransfer(order);
                    ExecuteTransfer(order);
                }
            }
            catch (Exception ex)
            {
                LogTransferFailed(order, ex);
                throw new TransferException("Transfer failed", ex);
            }
        }

        private void ValidateTransfer(Order order)
        {
            // 验证转账参数
            if (order.Amount <= 0)
                throw new ArgumentException("Invalid amount");
        }

        private void ExecuteTransfer(Order order)
        {
            // 执行实际转账
            Console.WriteLine($"Executing transfer for {order.Amount}");
        }

        private void LogTransferFailed(Order order, Exception ex)
        {
            Console.WriteLine($"Transfer failed for order {order.Id}: {ex.Message}");
        }
    }

    public class Order
    {
        public string Id { get; set; }
        public decimal Amount { get; set; }
        public string TransferType { get; set; }
    }

    public class TransferException : Exception
    {
        public TransferException(string message, Exception innerException) 
            : base(message, innerException)
        {
        }
    }
}