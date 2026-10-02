-- Fact Order Payments: Payment method details, installment terms, and financing indicators
SELECT
    p.order_id,
    p.payment_sequential,
    p.payment_type,
    p.payment_installments,
    ROUND(p.payment_amount, 2) AS payment_amount,
    CASE 
        WHEN p.payment_type = 'credit_card' THEN TRUE 
        ELSE FALSE 
    END AS is_credit_card_payment,
    CASE 
        WHEN p.payment_installments > 1 THEN TRUE 
        ELSE FALSE 
    END AS is_split_installment
FROM stg_payments p;
