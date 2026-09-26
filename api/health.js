export default function handler(req, res) {
    return res.status(200).json({
        status: 'ok',
        app: 'Tempo Wellbeing',
        version: '1.0.0',
        environment: 'vercel-serverless'
    });
}
