import './Skeleton.css';

export const Skeleton = ({ width, height, borderRadius, className = '' }) => {
    const style = {
        width: width || '100%',
        height: height || '20px',
        borderRadius: borderRadius || '4px',
    };

    return <div className={`skeleton-loader ${className}`} style={style}></div>;
};

export const SkeletonTable = ({ rows = 5, columns = 5 }) => {
    return (
        <div className="skeleton-table-container">
            <div className="skeleton-table-header">
                {[...Array(columns)].map((_, i) => (
                    <Skeleton key={i} height="30px" />
                ))}
            </div>
            {[...Array(rows)].map((_, rowIndex) => (
                <div key={rowIndex} className="skeleton-table-row">
                    {[...Array(columns)].map((_, colIndex) => (
                        <Skeleton key={colIndex} height="20px" />
                    ))}
                </div>
            ))}
        </div>
    );
};
